"""Summarize final sprint experiment outputs for report integration."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "results_100pt" / "summaries"


def read_metric_average(path: Path) -> tuple[int, float, float] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        return None
    return (
        len(rows),
        float(np.mean([float(row["psnr"]) for row in rows])),
        float(np.mean([float(row["ssim"]) for row in rows])),
    )


def collect_model_rows() -> list[dict[str, str | int | float]]:
    candidates = [
        ("Bicubic DIV2K", PROJECT_ROOT / "results" / "bicubic_x2_eval_metrics.csv"),
        ("IMDN 50ep DIV2K", PROJECT_ROOT / "results_10pt" / "div2k" / "imdn_no_edge_50ep_x2_eval_metrics.csv"),
        ("IDB-IMDN smoke", PROJECT_ROOT / "results_100pt" / "idb_imdn_smoke_x2_eval_metrics.csv"),
        ("IDB-IMDN 20ep", PROJECT_ROOT / "results_100pt" / "idb_imdn_20ep_x2_eval_metrics.csv"),
    ]
    rows: list[dict[str, str | int | float]] = []
    for name, path in candidates:
        metrics = read_metric_average(path)
        if metrics is None:
            continue
        rows.append({
            "experiment": name,
            "images": metrics[0],
            "avg_psnr": metrics[1],
            "avg_ssim": metrics[2],
            "source_csv": str(path.relative_to(PROJECT_ROOT)),
        })
    return rows


def collect_self_ensemble_rows() -> list[dict[str, str | int | float]]:
    root = PROJECT_ROOT / "results_100pt" / "self_ensemble"
    rows: list[dict[str, str | int | float]] = []
    if not root.exists():
        return rows
    for summary_path in sorted(root.glob("*_self_ensemble_summary.csv")):
        with summary_path.open("r", encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                rows.append({
                    "dataset": row["dataset"],
                    "mode": row["mode"],
                    "images": int(row["images"]),
                    "avg_psnr": float(row["avg_psnr"]),
                    "avg_ssim": float(row["avg_ssim"]),
                    "source_csv": str(summary_path.relative_to(PROJECT_ROOT)),
                })
    return rows


def write_csv(path: Path, rows: list[dict[str, str | int | float]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_rows = collect_model_rows()
    self_rows = collect_self_ensemble_rows()
    write_csv(
        OUTPUT_DIR / "model_comparison_100pt.csv",
        model_rows,
        ["experiment", "images", "avg_psnr", "avg_ssim", "source_csv"],
    )
    write_csv(
        OUTPUT_DIR / "self_ensemble_comparison_100pt.csv",
        self_rows,
        ["dataset", "mode", "images", "avg_psnr", "avg_ssim", "source_csv"],
    )
    print(f"Saved model summary rows: {len(model_rows)}")
    print(f"Saved self-ensemble summary rows: {len(self_rows)}")


if __name__ == "__main__":
    main()
