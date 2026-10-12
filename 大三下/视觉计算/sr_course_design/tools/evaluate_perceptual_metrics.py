"""Evaluate LPIPS and NIQE for super-resolution outputs.

This script intentionally keeps PyTorch/LPIPS/PyIQA optional. If they are not
installed, it reports the exact install command instead of silently skipping the
metrics.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute LPIPS/NIQE for SR result folders.")
    parser.add_argument("--target", required=True, type=Path, help="HR target directory")
    parser.add_argument("--result", action="append", required=True, help="Label=directory, can be repeated")
    parser.add_argument("--scale", default=2, type=int)
    parser.add_argument("--max-images", default=0, type=int, help="0 means all images")
    parser.add_argument("--output", default="./results_10pt/perceptual/perceptual_metrics.csv", type=Path)
    parser.add_argument("--summary", default="./results_10pt/perceptual/perceptual_summary.csv", type=Path)
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_optional_metrics():
    try:
        import lpips
        import pyiqa
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "Missing perceptual metric dependencies. Install them with:\n"
            "pip install torch torchvision lpips pyiqa -i https://pypi.tuna.tsinghua.edu.cn/simple"
        ) from exc

    lpips_metric = lpips.LPIPS(net="alex")
    lpips_metric.eval()
    niqe_metric = pyiqa.create_metric("niqe", device="cpu")
    return torch, lpips_metric, niqe_metric


def parse_result(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise ValueError(f"Expected Label=directory, got: {spec}")
    label, path = spec.split("=", 1)
    return label.strip(), resolve(Path(path.strip()))


def crop_border(image: Image.Image, scale: int) -> Image.Image:
    if scale <= 0:
        return image
    width, height = image.size
    if width <= scale * 2 or height <= scale * 2:
        return image
    return image.crop((scale, scale, width - scale, height - scale))


def image_to_lpips_tensor(torch_module, image: Image.Image):
    array = np.asarray(image.convert("RGB"), dtype=np.float32) / 127.5 - 1.0
    tensor = torch_module.from_numpy(array).permute(2, 0, 1).unsqueeze(0)
    return tensor


def image_to_niqe_tensor(torch_module, image: Image.Image):
    array = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    tensor = torch_module.from_numpy(array).permute(2, 0, 1).unsqueeze(0)
    return tensor


def evaluate_pair(torch_module, lpips_metric, niqe_metric, prediction_path: Path, target_path: Path, scale: int) -> tuple[float, float]:
    prediction = crop_border(Image.open(prediction_path).convert("RGB"), scale)
    target = crop_border(Image.open(target_path).convert("RGB"), scale)
    if prediction.size != target.size:
        prediction = prediction.resize(target.size, Image.BICUBIC)

    with torch_module.no_grad():
        lpips_value = float(lpips_metric(image_to_lpips_tensor(torch_module, prediction), image_to_lpips_tensor(torch_module, target)).item())
        try:
            niqe_value = float(niqe_metric(str(prediction_path)).item())
        except Exception:
            niqe_value = float(niqe_metric(image_to_niqe_tensor(torch_module, prediction)).item())
    return lpips_value, niqe_value


def main() -> None:
    args = parse_args()
    torch_module, lpips_metric, niqe_metric = load_optional_metrics()
    target_dir = resolve(args.target)
    output_path = resolve(args.output)
    summary_path = resolve(args.summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    summaries: list[dict[str, str]] = []
    for label, result_dir in [parse_result(spec) for spec in args.result]:
        result_files = sorted(path for path in result_dir.iterdir() if path.suffix.lower() in {".png", ".jpg", ".jpeg"})
        if args.max_images > 0:
            result_files = result_files[: args.max_images]
        lpips_values: list[float] = []
        niqe_values: list[float] = []
        for prediction_path in result_files:
            target_path = target_dir / prediction_path.name
            if not target_path.exists():
                continue
            lpips_value, niqe_value = evaluate_pair(torch_module, lpips_metric, niqe_metric, prediction_path, target_path, args.scale)
            lpips_values.append(lpips_value)
            niqe_values.append(niqe_value)
            rows.append({
                "method": label,
                "filename": prediction_path.name,
                "lpips": f"{lpips_value:.6f}",
                "niqe": f"{niqe_value:.6f}",
            })
        summaries.append({
            "method": label,
            "num_images": str(len(lpips_values)),
            "lpips": f"{float(np.mean(lpips_values)):.6f}" if lpips_values else "nan",
            "niqe": f"{float(np.mean(niqe_values)):.6f}" if niqe_values else "nan",
        })

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["method", "filename", "lpips", "niqe"])
        writer.writeheader()
        writer.writerows(rows)

    with summary_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["method", "num_images", "lpips", "niqe"])
        writer.writeheader()
        writer.writerows(summaries)

    print(f"Saved perceptual metrics: {output_path}")
    print(f"Saved perceptual summary: {summary_path}")


if __name__ == "__main__":
    main()
