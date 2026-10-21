"""Summarize experiment CSV metrics, model size, and training time."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


EXPERIMENTS = [
    ("Bicubic", "bicubic_x2_eval_metrics.csv", ""),
    ("SRCNN 2ep", "srcnn_x2_eval_metrics.csv", "srcnn_x2_metrics.csv"),
    ("SRCNN 20ep", "srcnn_20ep_x2_eval_metrics.csv", "srcnn_x2_20ep_metrics.csv"),
    ("IMDN 5ep", "imdn_x2_no_edge_eval_metrics.csv", "imdn_x2_no_edge_metrics.csv"),
    ("IMDN 20ep", "imdn_x2_no_edge_20ep_eval_metrics.csv", "imdn_x2_no_edge_20ep_metrics.csv"),
    ("IMDN 50ep", "imdn_x2_no_edge_50ep_eval_metrics.csv", "imdn_x2_no_edge_50ep_metrics.csv"),
    ("CA-IMDN 20ep", "ca_imdn_no_edge_20ep_x2_eval_metrics.csv", "ca_imdn_x2_no_edge_20ep_metrics.csv"),
    ("CA-IMDN 50ep", "ca_imdn_no_edge_50ep_x2_eval_metrics.csv", "ca_imdn_x2_no_edge_50ep_metrics.csv"),
    ("CA-IMDN Edge 0.01 20ep", "ca_imdn_edge_w001_20ep_x2_eval_metrics.csv", "ca_imdn_x2_edge_w001_20ep_metrics.csv"),
    ("IMDN width16 20ep", "imdn_width16_20ep_x2_eval_metrics.csv", "imdn_x2_width16_20ep_metrics.csv"),
    ("IMDN width48 20ep", "imdn_width48_20ep_x2_eval_metrics.csv", "imdn_x2_width48_20ep_metrics.csv"),
    ("IMDN depth2 20ep", "imdn_depth2_20ep_x2_eval_metrics.csv", "imdn_x2_depth2_20ep_metrics.csv"),
    ("IMDN depth6 20ep", "imdn_depth6_20ep_x2_eval_metrics.csv", "imdn_x2_depth6_20ep_metrics.csv"),
    ("IMDN StepLR 20ep", "imdn_no_edge_20ep_step_lr_x2_eval_metrics.csv", "imdn_x2_no_edge_20ep_step_lr_metrics.csv"),
    ("IMDN CosineLR 20ep", "imdn_no_edge_20ep_cosine_lr_x2_eval_metrics.csv", "imdn_x2_no_edge_20ep_cosine_lr_metrics.csv"),
    ("CA-IMDN CosineLR 20ep", "ca_imdn_no_edge_20ep_cosine_lr_x2_eval_metrics.csv", "ca_imdn_x2_no_edge_20ep_cosine_lr_metrics.csv"),
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def metric_summary(metrics_path: Path) -> tuple[float, float, int] | None:
    if not metrics_path.exists():
        return None
    rows = read_rows(metrics_path)
    if not rows:
        return None
    return (
        float(np.mean([float(row["psnr"]) for row in rows])),
        float(np.mean([float(row["ssim"]) for row in rows])),
        len(rows),
    )


def timing_summary(log_path: Path) -> tuple[float, float] | None:
    if not log_path.exists():
        return None
    rows = read_rows(log_path)
    if not rows or "epoch_time_sec" not in rows[0]:
        return None
    times = [float(row["epoch_time_sec"]) for row in rows if row.get("epoch_time_sec")]
    if not times:
        return None
    return float(sum(times)), float(np.mean(times))


def write_summary() -> None:
    output_dir = PROJECT_ROOT / "results" / "summaries"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "experiment_summary.csv"
    md_path = output_dir / "experiment_summary.md"

    records = []
    for label, metric_file, log_file in EXPERIMENTS:
        metric = metric_summary(PROJECT_ROOT / "results" / metric_file)
        timing = timing_summary(PROJECT_ROOT / "logs" / log_file) if log_file else None
        if metric is None:
            continue
        records.append(
            {
                "method": label,
                "psnr": f"{metric[0]:.4f}",
                "ssim": f"{metric[1]:.4f}",
                "num_images": str(metric[2]),
                "total_train_time_sec": "" if timing is None else f"{timing[0]:.2f}",
                "avg_epoch_time_sec": "" if timing is None else f"{timing[1]:.2f}",
            }
        )

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        fieldnames = ["method", "psnr", "ssim", "num_images", "total_train_time_sec", "avg_epoch_time_sec"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    lines = ["# Experiment Summary", ""]
    lines.append("| Method | PSNR | SSIM | Images | Total train time / s | Avg epoch / s |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in records:
        lines.append(
            f"| {row['method']} | {row['psnr']} | {row['ssim']} | {row['num_images']} | "
            f"{row['total_train_time_sec']} | {row['avg_epoch_time_sec']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {csv_path}")
    print(f"Saved {md_path}")


if __name__ == "__main__":
    write_summary()
