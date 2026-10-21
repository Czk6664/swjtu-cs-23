"""Generate report figures for the 100-point sprint when result CSVs exist."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = PROJECT_ROOT / "report" / "figures"
SUMMARY_DIR = PROJECT_ROOT / "results_100pt" / "summaries"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _setup_plot() -> None:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def save_self_ensemble_chart() -> None:
    path = SUMMARY_DIR / "self_ensemble_comparison_100pt.csv"
    if not path.exists():
        return
    rows = _read_csv(path)
    if len(rows) < 2:
        return
    _setup_plot()
    labels = [f"{row['dataset']}\n{row['mode']}" for row in rows]
    psnr_values = [float(row["avg_psnr"]) for row in rows]
    ssim_values = [float(row["avg_ssim"]) for row in rows]
    colors = ["#4b8f29" if row["mode"] == "self_ensemble" else "#6c7a89" for row in rows]

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2), dpi=200)
    axes[0].bar(labels, psnr_values, color=colors, width=0.55)
    axes[0].set_title("Normal vs Self-Ensemble: PSNR")
    axes[0].set_ylabel("PSNR (dB)")
    axes[0].grid(axis="y", alpha=0.2)

    axes[1].bar(labels, ssim_values, color=colors, width=0.55)
    axes[1].set_title("Normal vs Self-Ensemble: SSIM")
    axes[1].set_ylabel("SSIM")
    axes[1].grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "self_ensemble_metrics.png", bbox_inches="tight")
    plt.close(fig)


def save_idb_model_chart() -> None:
    path = SUMMARY_DIR / "model_comparison_100pt.csv"
    if not path.exists():
        return
    rows = _read_csv(path)
    if len(rows) < 2:
        return
    _setup_plot()
    labels = [row["experiment"].replace(" ", "\n") for row in rows]
    psnr_values = [float(row["avg_psnr"]) for row in rows]
    ssim_values = [float(row["avg_ssim"]) for row in rows]
    colors = ["#1b7f5f" if "IDB" in row["experiment"] else "#5b8db8" for row in rows]

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.2), dpi=200)
    axes[0].bar(labels, psnr_values, color=colors, width=0.55)
    axes[0].set_title("IDB-IMDN-Lite Comparison: PSNR")
    axes[0].set_ylabel("PSNR (dB)")
    axes[0].grid(axis="y", alpha=0.2)

    axes[1].bar(labels, ssim_values, color=colors, width=0.55)
    axes[1].set_title("IDB-IMDN-Lite Comparison: SSIM")
    axes[1].set_ylabel("SSIM")
    axes[1].grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "idb_imdn_comparison.png", bbox_inches="tight")
    plt.close(fig)


def _resize_with_label(path: Path, label: str, size: tuple[int, int]) -> Image.Image | None:
    if not path.exists():
        return None
    image = Image.open(path).convert("RGB")
    image.thumbnail(size)
    canvas = Image.new("RGB", size, "white")
    left = (size[0] - image.width) // 2
    top = (size[1] - image.height) // 2
    canvas.paste(image, (left, top))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, size[0], 22), fill="white")
    draw.text((6, 4), label, fill="black")
    return canvas


def save_self_ensemble_visual_grid(sample_name: str = "0821.png") -> None:
    root = PROJECT_ROOT / "results_100pt" / "self_ensemble"
    if not root.exists():
        return
    candidates = [
        ("LR", PROJECT_ROOT / "data" / "eval" / "LR" / sample_name),
        ("Normal", root / "DIV2K_imdn_normal_x2" / sample_name),
        ("Self-Ensemble", root / "DIV2K_imdn_self_ensemble_x2" / sample_name),
        ("HR", PROJECT_ROOT / "data" / "eval" / "HR" / sample_name),
    ]
    tiles = [tile for label, path in candidates if (tile := _resize_with_label(path, label, (240, 180))) is not None]
    if len(tiles) < 3:
        return
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    grid = Image.new("RGB", (240 * len(tiles), 180), "white")
    for index, tile in enumerate(tiles):
        grid.paste(tile, (index * 240, 0))
    grid.save(FIG_DIR / "self_ensemble_visual_grid.png")


def main() -> None:
    save_self_ensemble_chart()
    save_idb_model_chart()
    save_self_ensemble_visual_grid()


if __name__ == "__main__":
    main()
