"""
SAHI (Slicing Aided Hyper Inference) for Small Object Detection
Paper: IEEE ICIP 2022, arXiv:2202.06934

Usage:
    cd traffic_sign_detection
    python experiments/sahi/run_sahi.py --weights runs/tt100k/yolo11n_704_e50/weights/best.pt --source data/tt100k_yolo/images/val
"""

import argparse
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # traffic_sign_detection/


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--weights", required=True, help="YOLO weights path")
    p.add_argument("--source", default=str(ROOT / "data" / "tt100k_yolo" / "images" / "val"))
    p.add_argument("--slice-size", type=int, default=640)
    p.add_argument("--overlap", type=float, default=0.2)
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--device", default="0")
    p.add_argument("--output", default=str(ROOT / "runs" / "sahi"))
    return p.parse_args()


def main():
    args = parse_args()

    try:
        from sahi import AutoDetectionModel
        from sahi.predict import get_sliced_prediction
    except ImportError:
        print("ERROR: pip install sahi")
        return

    print(f"[SAHI] Loading model: {args.weights}")
    model = AutoDetectionModel.from_pretrained(
        model_type="ultralytics",
        model_path=args.weights,
        confidence_threshold=args.conf,
        device=f"cuda:{args.device}" if args.device != "cpu" else "cpu",
    )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    source = Path(args.source)
    images = list(source.glob("*.jpg")) + list(source.glob("*.png"))
    print(f"[SAHI] {len(images)} images, slice={args.slice_size}, overlap={args.overlap}")

    results = []
    total_time = 0

    for i, img_path in enumerate(images):
        t0 = time.time()
        result = get_sliced_prediction(
            image=str(img_path), detection_model=model,
            slice_height=args.slice_size, slice_width=args.slice_size,
            overlap_height_ratio=args.overlap, overlap_width_ratio=args.overlap,
            perform_standard_pred=True, postprocess_type="NMS",
            postprocess_match_threshold=0.5, verbose=0,
        )
        elapsed = time.time() - t0
        total_time += elapsed

        n_dets = len(result.object_prediction_list)
        classes = {}
        for pred in result.object_prediction_list:
            cls = pred.category.name
            classes[cls] = classes.get(cls, 0) + 1

        results.append({"image": img_path.name, "detections": n_dets, "classes": classes, "time": elapsed})

        if (i + 1) % 50 == 0 or (i + 1) == len(images):
            print(f"  [{i+1}/{len(images)}] {img_path.name}: {n_dets} dets, {elapsed:.2f}s")

    avg = total_time / len(images) if images else 0
    total_dets = sum(r["detections"] for r in results)
    print(f"\n[SAHI] Done: {len(images)} images, {total_dets} total dets, avg {avg:.3f}s/img")

    with open(output_dir / "sahi_results.json", "w") as f:
        json.dump({"config": vars(args), "summary": {"images": len(images), "total_dets": total_dets, "avg_time": avg}, "per_image": results}, f, indent=2)
    print(f"  Saved: {output_dir / 'sahi_results.json'}")


if __name__ == "__main__":
    main()
