"""Evaluation entrypoint for super-resolution course project."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image


def crop_border(image: np.ndarray, border: int) -> np.ndarray:
    """Crop border pixels for metric evaluation."""

    if border <= 0:
        return image
    return image[border:-border, border:-border]


def rgb_to_y_channel(image: np.ndarray) -> np.ndarray:
    """Convert RGB image to Y channel."""

    image = image.astype(np.float32)
    return 16.0 + (64.738 * image[:, :, 0] + 129.057 * image[:, :, 1] + 25.064 * image[:, :, 2]) / 256.0


def calculate_psnr(pred: np.ndarray, target: np.ndarray) -> float:
    """Compute PSNR score for uint8 or float arrays."""

    pred = pred.astype(np.float32)
    target = target.astype(np.float32)
    mse = np.mean((pred - target) ** 2)
    if mse == 0:
        return float("inf")
    return float(20 * np.log10(255.0 / np.sqrt(mse)))


def calculate_ssim(pred: np.ndarray, target: np.ndarray) -> float:
    """Compute a lightweight global SSIM score."""

    pred = pred.astype(np.float64)
    target = target.astype(np.float64)

    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2

    mu_pred = pred.mean()
    mu_target = target.mean()
    sigma_pred = pred.var()
    sigma_target = target.var()
    sigma_cross = ((pred - mu_pred) * (target - mu_target)).mean()

    numerator = (2 * mu_pred * mu_target + c1) * (2 * sigma_cross + c2)
    denominator = (mu_pred ** 2 + mu_target ** 2 + c1) * (sigma_pred + sigma_target + c2)
    return float(numerator / denominator) if denominator != 0 else 1.0


def load_image(image_path: Path) -> np.ndarray:
    """Load image as RGB uint8 array."""

    return np.array(Image.open(image_path).convert("RGB"), dtype=np.uint8)


def evaluate_directory(result_dir: str | Path, target_dir: str | Path, scale: int, use_y_channel: bool, csv_path: str | Path | None) -> None:
    """Evaluate generated results against HR targets."""

    result_path = Path(result_dir)
    target_path = Path(target_dir)
    if not result_path.exists():
        raise FileNotFoundError(f"Result directory does not exist: {result_path}")
    if not target_path.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_path}")

    rows: list[dict[str, float | str]] = []
    for prediction_path in sorted(path for path in result_path.iterdir() if path.is_file()):
        reference_path = target_path / prediction_path.name
        if not reference_path.exists():
            continue

        prediction = crop_border(load_image(prediction_path), scale)
        target = crop_border(load_image(reference_path), scale)
        if prediction.shape != target.shape:
            raise ValueError(f"Shape mismatch for {prediction_path.name}: {prediction.shape} vs {target.shape}")

        if use_y_channel:
            prediction_metric = rgb_to_y_channel(prediction)
            target_metric = rgb_to_y_channel(target)
        else:
            prediction_metric = prediction
            target_metric = target

        psnr_value = calculate_psnr(prediction_metric, target_metric)
        ssim_value = calculate_ssim(prediction_metric, target_metric)
        rows.append({"filename": prediction_path.name, "psnr": psnr_value, "ssim": ssim_value})
        print(f"{prediction_path.name}: PSNR={psnr_value:.4f}, SSIM={ssim_value:.4f}")

    if not rows:
        raise ValueError("No matching prediction/target image pairs were found.")

    avg_psnr = sum(float(row["psnr"]) for row in rows) / len(rows)
    avg_ssim = sum(float(row["ssim"]) for row in rows) / len(rows)
    print(f"Average PSNR: {avg_psnr:.4f}")
    print(f"Average SSIM: {avg_ssim:.4f}")

    if csv_path is not None:
        resolved_csv = Path(csv_path)
        resolved_csv.parent.mkdir(parents=True, exist_ok=True)
        with resolved_csv.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["filename", "psnr", "ssim"])
            writer.writeheader()
            writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="Evaluate SR images with PSNR and SSIM")
    parser.add_argument("--results", required=True, type=str)
    parser.add_argument("--targets", required=True, type=str)
    parser.add_argument("--scale", default=2, type=int)
    parser.add_argument("--rgb", action="store_true")
    parser.add_argument("--csv", default="", type=str)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    evaluate_directory(
        result_dir=args.results,
        target_dir=args.targets,
        scale=args.scale,
        use_y_channel=not args.rgb,
        csv_path=args.csv or None,
    )
