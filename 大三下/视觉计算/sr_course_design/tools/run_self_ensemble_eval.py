"""Run normal and self-ensemble SR inference on one paired LR/HR dataset."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.datasets.sr_dataset import denormalize_image, image_to_tensor, save_image
from src.eval import calculate_psnr, calculate_ssim, crop_border, rgb_to_y_channel
from src.infer import bicubic_upscale, build_model, collect_inputs, load_checkpoint_if_available, load_mindspore, run_inference
from src.self_ensemble import ENSEMBLE_TRANSFORMS, apply_transform, average_predictions, invert_transform


def _load_rgb(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.uint8)


def _model_predict_float(model, ms, image: np.ndarray) -> np.ndarray:
    input_tensor = ms.Tensor(np.expand_dims(image_to_tensor(image), axis=0))
    output = model(input_tensor).asnumpy()[0]
    return np.transpose(np.clip(output, 0.0, 1.0), (1, 2, 0)).astype(np.float32)


def run_self_ensemble(
    model_name: str,
    scale: int,
    input_path: str | Path,
    output_path: str | Path,
    num_features: int,
    checkpoint_path: str | None = None,
    num_blocks: int = 4,
) -> None:
    """Run deterministic self-ensemble inference."""

    input_files = collect_inputs(input_path)
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    normalized_name = model_name.lower()
    model = build_model(normalized_name, scale, num_features, num_blocks=num_blocks)
    ms = None
    if model is not None:
        ms = load_mindspore()
        ms.set_context(mode=ms.PYNATIVE_MODE, device_target="CPU")
        if not checkpoint_path:
            raise ValueError("Self-ensemble learned-model inference requires --checkpoint.")
        load_checkpoint_if_available(model, checkpoint_path)
        model.set_train(False)

    for image_path in input_files:
        image = _load_rgb(image_path)
        predictions: list[np.ndarray] = []
        for transform in ENSEMBLE_TRANSFORMS:
            transformed = apply_transform(image, transform)
            if normalized_name == "bicubic":
                prediction_uint8 = bicubic_upscale(transformed, scale)
                prediction = prediction_uint8.astype(np.float32) / 255.0
            else:
                prediction = _model_predict_float(model, ms, transformed)
            restored = invert_transform(prediction, transform)
            predictions.append(restored)

        averaged = average_predictions(predictions)
        target_path = output_dir / image_path.name
        save_image(denormalize_image(averaged), target_path)
        print(f"Saved self-ensemble result: {target_path}")


def evaluate_to_csv(
    result_dir: str | Path,
    target_dir: str | Path,
    scale: int,
    use_y_channel: bool,
    csv_path: str | Path,
) -> tuple[int, float, float]:
    """Evaluate a result directory and return count/average metrics."""

    result_path = Path(result_dir)
    target_path = Path(target_dir)
    if not result_path.exists():
        raise FileNotFoundError(f"Result directory does not exist: {result_path}")
    if not target_path.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_path}")

    rows: list[dict[str, str | float]] = []
    for prediction_path in sorted(path for path in result_path.iterdir() if path.is_file()):
        reference_path = target_path / prediction_path.name
        if not reference_path.exists():
            continue
        prediction = crop_border(_load_rgb(prediction_path), scale)
        target = crop_border(_load_rgb(reference_path), scale)
        if prediction.shape != target.shape:
            raise ValueError(f"Shape mismatch for {prediction_path.name}: {prediction.shape} vs {target.shape}")
        if use_y_channel:
            prediction_metric = rgb_to_y_channel(prediction)
            target_metric = rgb_to_y_channel(target)
        else:
            prediction_metric = prediction
            target_metric = target
        rows.append({
            "filename": prediction_path.name,
            "psnr": calculate_psnr(prediction_metric, target_metric),
            "ssim": calculate_ssim(prediction_metric, target_metric),
        })

    if not rows:
        raise ValueError(f"No matching prediction/target pairs found for {result_path} and {target_path}")

    output_csv = Path(csv_path)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["filename", "psnr", "ssim"])
        writer.writeheader()
        writer.writerows(rows)

    avg_psnr = float(np.mean([float(row["psnr"]) for row in rows]))
    avg_ssim = float(np.mean([float(row["ssim"]) for row in rows]))
    return len(rows), avg_psnr, avg_ssim


def write_summary(rows: list[dict[str, str | int | float]], output_path: str | Path) -> None:
    """Write normal-vs-self-ensemble summary rows."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["dataset", "mode", "images", "avg_psnr", "avg_ssim"])
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run normal and self-ensemble SR evaluation")
    parser.add_argument("--dataset-name", default="DIV2K", type=str)
    parser.add_argument("--input", required=True, type=str, help="LR image directory or file")
    parser.add_argument("--target", required=True, type=str, help="HR image directory")
    parser.add_argument("--model", default="imdn", choices=["bicubic", "imdn", "ca_imdn", "idb_imdn", "srcnn"])
    parser.add_argument("--scale", default=2, type=int)
    parser.add_argument("--num-features", default=32, type=int)
    parser.add_argument("--num-blocks", default=4, type=int)
    parser.add_argument("--checkpoint", default="", type=str)
    parser.add_argument("--output-root", default="./results_100pt/self_ensemble", type=str)
    parser.add_argument("--rgb", action="store_true")
    parser.add_argument("--skip-normal", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_root)
    normal_dir = output_root / f"{args.dataset_name}_{args.model}_normal_x{args.scale}"
    ensemble_dir = output_root / f"{args.dataset_name}_{args.model}_self_ensemble_x{args.scale}"
    normal_csv = output_root / f"{args.dataset_name}_{args.model}_normal_metrics.csv"
    ensemble_csv = output_root / f"{args.dataset_name}_{args.model}_self_ensemble_metrics.csv"
    summary_csv = output_root / f"{args.dataset_name}_{args.model}_self_ensemble_summary.csv"

    if args.model != "bicubic" and not args.checkpoint:
        raise ValueError("Learned-model self-ensemble evaluation requires --checkpoint.")
    if not Path(args.input).exists():
        raise FileNotFoundError(f"Input path does not exist: {args.input}")
    if not Path(args.target).exists():
        raise FileNotFoundError(f"Target path does not exist: {args.target}")

    if not args.skip_normal:
        run_inference(
            model_name=args.model,
            scale=args.scale,
            input_path=args.input,
            output_path=str(normal_dir),
            num_features=args.num_features,
            checkpoint_path=args.checkpoint or None,
            num_blocks=args.num_blocks,
        )
    elif not normal_dir.exists():
        raise FileNotFoundError(f"--skip-normal was set but normal output directory does not exist: {normal_dir}")

    run_self_ensemble(
        model_name=args.model,
        scale=args.scale,
        input_path=args.input,
        output_path=ensemble_dir,
        num_features=args.num_features,
        checkpoint_path=args.checkpoint or None,
        num_blocks=args.num_blocks,
    )

    rows: list[dict[str, str | int | float]] = []
    normal_count, normal_psnr, normal_ssim = evaluate_to_csv(
        result_dir=normal_dir,
        target_dir=args.target,
        scale=args.scale,
        use_y_channel=not args.rgb,
        csv_path=normal_csv,
    )
    rows.append({
        "dataset": args.dataset_name,
        "mode": "normal",
        "images": normal_count,
        "avg_psnr": normal_psnr,
        "avg_ssim": normal_ssim,
    })
    ensemble_count, ensemble_psnr, ensemble_ssim = evaluate_to_csv(
        result_dir=ensemble_dir,
        target_dir=args.target,
        scale=args.scale,
        use_y_channel=not args.rgb,
        csv_path=ensemble_csv,
    )
    rows.append({
        "dataset": args.dataset_name,
        "mode": "self_ensemble",
        "images": ensemble_count,
        "avg_psnr": ensemble_psnr,
        "avg_ssim": ensemble_ssim,
    })
    write_summary(rows, summary_csv)
    print(f"Saved self-ensemble summary: {summary_csv}")


if __name__ == "__main__":
    main()
