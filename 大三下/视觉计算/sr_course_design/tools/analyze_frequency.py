"""Create FFT magnitude comparison from real SR outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def spectrum(path: Path) -> np.ndarray:
    image = Image.open(path).convert("L")
    array = np.asarray(image, dtype=np.float32)
    fft = np.fft.fftshift(np.fft.fft2(array))
    magnitude = np.log1p(np.abs(fft))
    magnitude -= magnitude.min()
    max_value = magnitude.max()
    if max_value > 1e-8:
        magnitude /= max_value
    return magnitude


def build_frequency_figure(filename: str, output: Path) -> None:
    candidates = [
        ("LR", PROJECT_ROOT / "data" / "eval" / "LR" / filename),
        ("Bicubic", PROJECT_ROOT / "results" / "bicubic_x2_eval" / filename),
        ("IMDN 50ep", PROJECT_ROOT / "results" / "imdn_x2_no_edge_50ep_eval" / filename),
        ("CA-IMDN 50ep", PROJECT_ROOT / "results" / "ca_imdn_no_edge_50ep_x2_eval" / filename),
        ("HR", PROJECT_ROOT / "data" / "eval" / "HR" / filename),
    ]
    available = [(label, path) for label, path in candidates if path.exists()]
    if len(available) < 3:
        raise FileNotFoundError("Need at least LR, Bicubic, and HR/IMDN images to build frequency analysis.")

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(2, len(available), figsize=(3.0 * len(available), 5.8), dpi=180)
    if len(available) == 1:
        axes = np.array([[axes[0]], [axes[1]]])

    for index, (label, path) in enumerate(available):
        image = Image.open(path).convert("RGB")
        axes[0, index].imshow(image)
        axes[0, index].set_title(label)
        axes[0, index].axis("off")
        axes[1, index].imshow(spectrum(path), cmap="magma")
        axes[1, index].set_title(f"{label} FFT")
        axes[1, index].axis("off")

    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved frequency analysis: {output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate FFT frequency comparison figure")
    parser.add_argument("--filename", default="0821.png")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "report" / "figures" / "frequency_analysis.png")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_frequency_figure(args.filename, args.output)
