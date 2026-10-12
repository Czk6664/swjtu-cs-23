"""Summarize benchmark PSNR/SSIM CSV files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize benchmark metric CSVs.")
    parser.add_argument("--input-root", default="./results_10pt/benchmarks", type=Path)
    parser.add_argument("--output-csv", default="./results_10pt/benchmarks/benchmark_summary.csv", type=Path)
    parser.add_argument("--output-md", default="./results_10pt/benchmarks/benchmark_summary.md", type=Path)
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def parse_name(path: Path) -> tuple[str, str]:
    name = path.stem.removesuffix("_metrics")
    parts = name.split("_")
    benchmark = parts[0]
    model = "_".join(parts[1:-1]) if len(parts) >= 3 else "unknown"
    return benchmark, model


def read_metrics(path: Path) -> tuple[float, float, int]:
    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        return float("nan"), float("nan"), 0
    psnr = float(np.mean([float(row["psnr"]) for row in rows]))
    ssim = float(np.mean([float(row["ssim"]) for row in rows]))
    return psnr, ssim, len(rows)


def main() -> None:
    args = parse_args()
    input_root = resolve(args.input_root)
    output_csv = resolve(args.output_csv)
    output_md = resolve(args.output_md)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    summary: list[dict[str, str]] = []
    for metrics_path in sorted(input_root.glob("*_metrics.csv")):
        benchmark, model = parse_name(metrics_path)
        psnr, ssim, count = read_metrics(metrics_path)
        summary.append({
            "benchmark": benchmark,
            "model": model,
            "num_images": str(count),
            "psnr": f"{psnr:.4f}",
            "ssim": f"{ssim:.4f}",
            "source_csv": str(metrics_path.relative_to(PROJECT_ROOT)),
        })

    with output_csv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["benchmark", "model", "num_images", "psnr", "ssim", "source_csv"])
        writer.writeheader()
        writer.writerows(summary)

    with output_md.open("w", encoding="utf-8") as file:
        file.write("| Benchmark | Model | Images | PSNR | SSIM |\n")
        file.write("|---|---:|---:|---:|---:|\n")
        for row in summary:
            file.write(
                f"| {row['benchmark']} | {row['model']} | {row['num_images']} | {row['psnr']} | {row['ssim']} |\n"
            )

    print(f"Saved benchmark summary: {output_csv}")
    print(f"Saved benchmark markdown: {output_md}")


if __name__ == "__main__":
    main()
