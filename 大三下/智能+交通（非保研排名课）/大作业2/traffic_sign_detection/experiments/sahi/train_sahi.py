"""
SAHI (Slicing Aided Hyper Inference) for Small Object Detection
Paper: IEEE ICIP 2022, arXiv:2202.06934

Slices input images into overlapping tiles, runs YOLO inference on each tile,
and merges results with NMS. This effectively increases the resolution at which
small traffic signs are seen without changing the model architecture.

Usage:
    python train_sahi.py --weights runs/tt100k/yolo11n_704_e50/weights/best.pt --source data/tt100k_yolo/images/val
    python train_sahi.py --weights best.pt --source test.jpg --slice-size 640 --overlap 0.2

Requires: pip install sahi ultralytics
"""

import argparse
import json
import time
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="SAHI inference with YOLO on TT100K")
    parser.add_argument("--weights", required=True, help="Path to YOLO weights (.pt)")
    parser.add_argument("--source", required=True, help="Image or directory to run inference on")
    parser.add_argument("--slice-size", type=int, default=640, help="Tile size for slicing")
    parser.add_argument("--overlap", type=float, default=0.2, help="Overlap ratio between tiles")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--device", default="0", help="Device (cpu or 0)")
    parser.add_argument("--output", default="runs/sahi", help="Output directory")
    parser.add_argument("--eval-only", action="store_true", help="Run evaluation on TT100K val set")
    return parser.parse_args()


def run_sahi_inference(args):
    """Run SAHI sliced inference on images."""
    try:
        from sahi import AutoDetectionModel
        from sahi.predict import get_sliced_prediction
        from sahi.utils.cv import read_image
    except ImportError:
        print("ERROR: SAHI not installed. Run: pip install sahi")
        return

    # Load model
    print(f"[SAHI] Loading model: {args.weights}")
    detection_model = AutoDetectionModel.from_pretrained(
        model_type="ultralytics",
        model_path=args.weights,
        confidence_threshold=args.conf,
        device=f"cuda:{args.device}" if args.device != "cpu" else "cpu",
    )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    source = Path(args.source)
    if source.is_dir():
        images = list(source.glob("*.jpg")) + list(source.glob("*.png"))
    else:
        images = [source]

    print(f"[SAHI] Processing {len(images)} images with slice_size={args.slice_size}, overlap={args.overlap}")
    print(f"[SAHI] Output: {output_dir}")

    all_results = []
    total_time = 0

    for i, img_path in enumerate(images):
        start = time.time()
        result = get_sliced_prediction(
            image=str(img_path),
            detection_model=detection_model,
            slice_height=args.slice_size,
            slice_width=args.slice_size,
            overlap_height_ratio=args.overlap,
            overlap_width_ratio=args.overlap,
            perform_standard_pred=True,
            postprocess_type="NMS",
            postprocess_match_threshold=0.5,
            verbose=0,
        )
        elapsed = time.time() - start
        total_time += elapsed

        # Count detections
        n_dets = len(result.object_prediction_list)
        classes = {}
        for pred in result.object_prediction_list:
            cls = pred.category.name
            classes[cls] = classes.get(cls, 0) + 1

        all_results.append({
            "image": img_path.name,
            "detections": n_dets,
            "classes": classes,
            "time": elapsed,
        })

        if (i + 1) % 50 == 0 or (i + 1) == len(images):
            print(f"  [{i+1}/{len(images)}] {img_path.name}: {n_dets} dets, {elapsed:.2f}s")

    # Summary
    avg_time = total_time / len(images) if images else 0
    total_dets = sum(r["detections"] for r in all_results)
    print(f"\n[SAHI] Summary:")
    print(f"  Images: {len(images)}")
    print(f"  Total detections: {total_dets}")
    print(f"  Avg time/image: {avg_time:.3f}s")
    print(f"  Total time: {total_time:.1f}s")

    # Save results
    results_path = output_dir / "sahi_results.json"
    with open(results_path, "w") as f:
        json.dump({
            "config": {
                "weights": str(args.weights),
                "slice_size": args.slice_size,
                "overlap": args.overlap,
                "conf": args.conf,
            },
            "summary": {
                "images": len(images),
                "total_detections": total_dets,
                "avg_time": avg_time,
                "total_time": total_time,
            },
            "per_image": all_results,
        }, f, indent=2)
    print(f"  Results saved: {results_path}")


def run_eval_comparison(args):
    """Compare standard vs SAHI inference on TT100K val set."""
    from ultralytics import YOLO
    import numpy as np

    print(f"\n{'='*60}")
    print("Standard YOLO vs SAHI Comparison")
    print(f"{'='*60}")

    model = YOLO(args.weights)

    # Standard inference
    print("\n[1/2] Standard inference...")
    results_standard = model.val(
        data="configs/dataset/tt100k.yaml",
        imgsz=704,
        batch=8,
        device=args.device,
        verbose=False,
    )
    print(f"  mAP50:    {results_standard.box.map50:.4f}")
    print(f"  mAP50-95: {results_standard.box.map:.4f}")
    print(f"  Recall:   {results_standard.box.mr:.4f}")

    # SAHI inference (on val images)
    print("\n[2/2] SAHI inference...")
    val_dir = Path("data/tt100k_yolo/images/val")
    if val_dir.exists():
        run_sahi_inference(args)
    else:
        print(f"  Val directory not found: {val_dir}")


def main():
    args = parse_args()

    if args.eval_only:
        run_eval_comparison(args)
    else:
        run_sahi_inference(args)


if __name__ == "__main__":
    main()
