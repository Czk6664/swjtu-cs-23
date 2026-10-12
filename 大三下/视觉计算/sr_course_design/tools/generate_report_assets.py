from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = PROJECT_ROOT / "report" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def split_epoch_runs(rows: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    """Split appended training logs whenever the epoch counter restarts."""

    runs: list[list[dict[str, str]]] = []
    current: list[dict[str, str]] = []
    previous_epoch = 0
    for row in rows:
        epoch = int(row["epoch"])
        if current and epoch <= previous_epoch:
            runs.append(current)
            current = []
        current.append(row)
        previous_epoch = epoch
    if current:
        runs.append(current)
    return runs


def metric_average(path: Path) -> tuple[float, float] | None:
    if not path.exists():
        return None
    rows = read_csv(path)
    if not rows:
        return None
    return (
        float(np.mean([float(row["psnr"]) for row in rows])),
        float(np.mean([float(row["ssim"]) for row in rows])),
    )


def save_training_curve() -> None:
    rows = read_csv(PROJECT_ROOT / "logs" / "imdn_x2_metrics.csv")
    runs = split_epoch_runs(rows)
    rows = runs[-1]
    epochs = [int(row["epoch"]) for row in rows]
    train_loss = [float(row["train_loss"]) for row in rows]
    val_psnr = [float(row["val_psnr"]) for row in rows]
    val_ssim = [float(row["val_ssim"]) for row in rows]

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), dpi=200)

    axes[0].plot(epochs, train_loss, marker="o", color="#b24a2b", linewidth=2)
    axes[0].set_title(f"Training Loss (latest run, {len(rows)} epochs)")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("L1 + Edge Loss")
    axes[0].grid(alpha=0.25)

    axes[1].plot(epochs, val_psnr, marker="o", color="#1d6f8c", linewidth=2, label="PSNR")
    axes[1].plot(epochs, val_ssim, marker="s", color="#4b8f29", linewidth=2, label="SSIM")
    axes[1].set_title(f"Validation Metrics (latest run, {len(rows)} epochs)")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Value")
    axes[1].grid(alpha=0.25)
    axes[1].legend(frameon=False)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "training_curves.png", bbox_inches="tight")
    plt.close(fig)


def save_metric_bar() -> None:
    candidates = [
        ("Bicubic", PROJECT_ROOT / "results" / "bicubic_x2_eval_metrics.csv", "#c97b63"),
        ("SRCNN\n2ep", PROJECT_ROOT / "results" / "srcnn_x2_eval_metrics.csv", "#6c7a89"),
        ("IMDN+Edge\n5ep", PROJECT_ROOT / "results" / "imdn_x2_eval_metrics.csv", "#2c7a7b"),
        ("IMDN\n5ep", PROJECT_ROOT / "results" / "imdn_x2_no_edge_eval_metrics.csv", "#4b8f29"),
        ("IMDN\n20ep", PROJECT_ROOT / "results" / "imdn_x2_no_edge_20ep_eval_metrics.csv", "#6aa84f"),
        ("IMDN\n50ep", PROJECT_ROOT / "results_10pt" / "div2k" / "imdn_no_edge_50ep_x2_eval_metrics.csv", "#1b7f5f"),
    ]
    available: list[tuple[str, float, float, str]] = []
    for label, path, color in candidates:
        metrics = metric_average(path)
        if metrics is not None:
            available.append((label, metrics[0], metrics[1], color))

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), dpi=200)

    methods = [item[0] for item in available]
    psnr_values = [item[1] for item in available]
    ssim_values = [item[2] for item in available]
    colors = [item[3] for item in available]

    axes[0].bar(methods, psnr_values, color=colors, width=0.55)
    axes[0].set_title("Average PSNR on DIV2K val")
    axes[0].set_ylabel("PSNR (dB)")
    axes[0].grid(axis="y", alpha=0.2)
    axes[0].tick_params(axis="x", labelrotation=0)

    axes[1].bar(methods, ssim_values, color=colors, width=0.55)
    axes[1].set_title("Average SSIM on DIV2K val")
    axes[1].set_ylabel("SSIM")
    axes[1].grid(axis="y", alpha=0.2)
    axes[1].tick_params(axis="x", labelrotation=0)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "metric_bar.png", bbox_inches="tight")
    plt.close(fig)


def _metric_records(candidates: list[tuple[str, Path, str]]) -> list[tuple[str, float, float, str]]:
    available: list[tuple[str, float, float, str]] = []
    for label, path, color in candidates:
        metrics = metric_average(path)
        if metrics is not None:
            available.append((label, metrics[0], metrics[1], color))
    return available


def save_extended_experiment_bar() -> None:
    candidates = [
        ("Bicubic", PROJECT_ROOT / "results" / "bicubic_x2_eval_metrics.csv", "#c97b63"),
        ("SRCNN\n20ep", PROJECT_ROOT / "results" / "srcnn_20ep_x2_eval_metrics.csv", "#6c7a89"),
        ("IMDN\n50ep", PROJECT_ROOT / "results_10pt" / "div2k" / "imdn_no_edge_50ep_x2_eval_metrics.csv", "#1b7f5f"),
        ("IMDN\nwidth48", PROJECT_ROOT / "results" / "imdn_width48_20ep_x2_eval_metrics.csv", "#4b8f29"),
        ("CA-IMDN\n20ep", PROJECT_ROOT / "results" / "ca_imdn_no_edge_20ep_x2_eval_metrics.csv", "#5b8db8"),
        ("CA-IMDN\nEdge", PROJECT_ROOT / "results" / "ca_imdn_edge_w001_20ep_x2_eval_metrics.csv", "#8b6bb8"),
        ("CA-IMDN\nCosine", PROJECT_ROOT / "results" / "ca_imdn_no_edge_20ep_cosine_lr_x2_eval_metrics.csv", "#2c7a7b"),
        ("CA-IMDN\n50ep", PROJECT_ROOT / "results" / "ca_imdn_no_edge_50ep_x2_eval_metrics.csv", "#b24a2b"),
    ]
    available = _metric_records(candidates)
    if len(available) < 2:
        return

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    labels = [item[0] for item in available]
    psnr_values = [item[1] for item in available]
    ssim_values = [item[2] for item in available]
    colors = [item[3] for item in available]

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), dpi=200)
    axes[0].bar(labels, psnr_values, color=colors, width=0.55)
    axes[0].set_title("Extended Experiments: PSNR")
    axes[0].set_ylabel("PSNR (dB)")
    axes[0].grid(axis="y", alpha=0.2)

    axes[1].bar(labels, ssim_values, color=colors, width=0.55)
    axes[1].set_title("Extended Experiments: SSIM")
    axes[1].set_ylabel("SSIM")
    axes[1].grid(axis="y", alpha=0.2)

    for axis in axes:
        axis.tick_params(axis="x", labelrotation=0)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "extended_experiment_metrics.png", bbox_inches="tight")
    plt.close(fig)


def save_capacity_ablation_bar() -> None:
    candidates = [
        ("width16\ndepth4", PROJECT_ROOT / "results" / "imdn_width16_20ep_x2_eval_metrics.csv", 43104, "#7f8c8d"),
        ("width32\ndepth2", PROJECT_ROOT / "results" / "imdn_depth2_20ep_x2_eval_metrics.csv", 109248, "#6c7a89"),
        ("width32\ndepth4", PROJECT_ROOT / "results" / "imdn_x2_no_edge_20ep_eval_metrics.csv", 170688, "#4b8f29"),
        ("CA width32\ndepth4", PROJECT_ROOT / "results" / "ca_imdn_no_edge_20ep_x2_eval_metrics.csv", 172736, "#5b8db8"),
        ("width32\ndepth6", PROJECT_ROOT / "results" / "imdn_depth6_20ep_x2_eval_metrics.csv", 232128, "#8b6bb8"),
        ("width48\ndepth4", PROJECT_ROOT / "results" / "imdn_width48_20ep_x2_eval_metrics.csv", 382752, "#b24a2b"),
    ]
    available: list[tuple[str, float, float, int, str]] = []
    for label, path, params, color in candidates:
        metrics = metric_average(path)
        if metrics is not None:
            available.append((label, metrics[0], metrics[1], params, color))
    if len(available) < 2:
        return

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    labels = [item[0] for item in available]
    psnr_values = [item[1] for item in available]
    params_m = [item[3] / 1_000_000 for item in available]
    colors = [item[4] for item in available]

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.2), dpi=200)
    axes[0].bar(labels, psnr_values, color=colors, width=0.55)
    axes[0].set_title("Model Capacity Ablation: PSNR")
    axes[0].set_ylabel("PSNR (dB)")
    axes[0].grid(axis="y", alpha=0.2)

    axes[1].bar(labels, params_m, color=colors, width=0.55)
    axes[1].set_title("Model Capacity")
    axes[1].set_ylabel("Parameters (M)")
    axes[1].grid(axis="y", alpha=0.2)

    for axis in axes:
        axis.tick_params(axis="x", labelrotation=0)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "model_capacity_ablation.png", bbox_inches="tight")
    plt.close(fig)


def save_scheduler_ablation_bar() -> None:
    candidates = [
        ("IMDN\nfixed LR", PROJECT_ROOT / "results" / "imdn_x2_no_edge_20ep_eval_metrics.csv", "#4b8f29"),
        ("IMDN\nStepLR", PROJECT_ROOT / "results" / "imdn_no_edge_20ep_step_lr_x2_eval_metrics.csv", "#5b8db8"),
        ("IMDN\nCosineLR", PROJECT_ROOT / "results" / "imdn_no_edge_20ep_cosine_lr_x2_eval_metrics.csv", "#2c7a7b"),
        ("CA-IMDN\nfixed LR", PROJECT_ROOT / "results" / "ca_imdn_no_edge_20ep_x2_eval_metrics.csv", "#8b6bb8"),
        ("CA-IMDN\nCosineLR", PROJECT_ROOT / "results" / "ca_imdn_no_edge_20ep_cosine_lr_x2_eval_metrics.csv", "#b24a2b"),
    ]
    available = _metric_records(candidates)
    if len(available) < 2:
        return

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    labels = [item[0] for item in available]
    psnr_values = [item[1] for item in available]
    ssim_values = [item[2] for item in available]
    colors = [item[3] for item in available]

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.1), dpi=200)
    axes[0].bar(labels, psnr_values, color=colors, width=0.55)
    axes[0].set_title("Learning-rate Strategy: PSNR")
    axes[0].set_ylabel("PSNR (dB)")
    axes[0].grid(axis="y", alpha=0.2)

    axes[1].bar(labels, ssim_values, color=colors, width=0.55)
    axes[1].set_title("Learning-rate Strategy: SSIM")
    axes[1].set_ylabel("SSIM")
    axes[1].grid(axis="y", alpha=0.2)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "scheduler_ablation.png", bbox_inches="tight")
    plt.close(fig)


def save_training_time_bar() -> None:
    summary_path = PROJECT_ROOT / "results" / "summaries" / "experiment_summary_from_run3.csv"
    if not summary_path.exists():
        summary_path = PROJECT_ROOT / "results" / "summaries" / "experiment_summary.csv"
    if not summary_path.exists():
        return

    rows = [row for row in read_csv(summary_path) if row.get("total_train_time_sec")]
    rows = [
        row
        for row in rows
        if row["method"]
        in {
            "SRCNN 20ep",
            "CA-IMDN 20ep",
            "CA-IMDN 50ep",
            "CA-IMDN Edge 0.01 20ep",
            "IMDN width16 20ep",
            "IMDN width48 20ep",
            "IMDN depth2 20ep",
            "IMDN depth6 20ep",
            "IMDN StepLR 20ep",
            "IMDN CosineLR 20ep",
            "CA-IMDN CosineLR 20ep",
        }
    ]
    if not rows:
        return

    labels = [row["method"].replace(" ", "\n", 1) for row in rows]
    times = [float(row["total_train_time_sec"]) / 60.0 for row in rows]

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(11.5, 4.0), dpi=200)
    ax.bar(labels, times, color="#5b8db8", width=0.55)
    ax.set_title("Training Time of Extended Experiments")
    ax.set_ylabel("Total training time (min)")
    ax.grid(axis="y", alpha=0.2)
    ax.tick_params(axis="x", labelrotation=18)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "training_time_comparison.png", bbox_inches="tight")
    plt.close(fig)


def save_ca_imdn_early_stop_analysis() -> None:
    candidates = [
        ("CA-IMDN\n20ep", PROJECT_ROOT / "results" / "ca_imdn_no_edge_20ep_x2_eval_metrics.csv", "#5b8db8"),
        ("CA-IMDN Edge\n20ep", PROJECT_ROOT / "results" / "ca_imdn_edge_w001_20ep_x2_eval_metrics.csv", "#8b6bb8"),
        ("CA-IMDN Cosine\n20ep", PROJECT_ROOT / "results" / "ca_imdn_no_edge_20ep_cosine_lr_x2_eval_metrics.csv", "#2c7a7b"),
        ("CA-IMDN\n50ep", PROJECT_ROOT / "results" / "ca_imdn_no_edge_50ep_x2_eval_metrics.csv", "#b24a2b"),
    ]
    available = _metric_records(candidates)
    if len(available) < 2:
        return

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    labels = [item[0] for item in available]
    psnr_values = [item[1] for item in available]
    ssim_values = [item[2] for item in available]
    colors = [item[3] for item in available]

    best_index = int(np.argmax(psnr_values))

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), dpi=200)
    axes[0].bar(labels, psnr_values, color=colors, width=0.55)
    axes[0].scatter([best_index], [psnr_values[best_index]], color="#111111", zorder=3, s=42)
    axes[0].set_title("CA-IMDN Early-stop Evidence: PSNR")
    axes[0].set_ylabel("PSNR (dB)")
    axes[0].grid(axis="y", alpha=0.2)

    axes[1].bar(labels, ssim_values, color=colors, width=0.55)
    axes[1].set_title("CA-IMDN Early-stop Evidence: SSIM")
    axes[1].set_ylabel("SSIM")
    axes[1].grid(axis="y", alpha=0.2)

    for axis in axes:
        axis.tick_params(axis="x", labelrotation=0)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "ca_imdn_early_stop_analysis.png", bbox_inches="tight")
    plt.close(fig)


def save_edge_ablation_bar() -> None:
    candidates = [
        ("No Edge 5ep", PROJECT_ROOT / "results" / "imdn_x2_no_edge_eval_metrics.csv"),
        ("Edge 0.01 quick", PROJECT_ROOT / "results" / "imdn_edge_w001_quick_x2_eval_metrics.csv"),
        ("Edge 0.02 quick", PROJECT_ROOT / "results" / "imdn_edge_w002_quick_x2_eval_metrics.csv"),
        ("Laplacian quick", PROJECT_ROOT / "results" / "imdn_laplacian_quick_x2_eval_metrics.csv"),
        ("Edge 0.05", PROJECT_ROOT / "results" / "imdn_x2_eval_metrics.csv"),
        ("No Edge 20ep", PROJECT_ROOT / "results" / "imdn_x2_no_edge_20ep_eval_metrics.csv"),
        ("Edge 0.01 20ep", PROJECT_ROOT / "results" / "imdn_edge_w001_20ep_x2_eval_metrics.csv"),
    ]
    available: list[tuple[str, float, float]] = []
    for label, path in candidates:
        metrics = metric_average(path)
        if metrics is not None:
            available.append((label, metrics[0], metrics[1]))

    if len(available) < 2:
        return

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    labels = [item[0] for item in available]
    psnr_values = [item[1] for item in available]
    ssim_values = [item[2] for item in available]
    colors = ["#4b8f29", "#5b8db8", "#8b6bb8", "#b24a2b", "#2c7a7b", "#1b7f5f", "#6aa84f"][: len(available)]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=200)
    axes[0].bar(labels, psnr_values, color=colors, width=0.55)
    axes[0].set_title("Edge-loss Ablation: PSNR")
    axes[0].set_ylabel("PSNR (dB)")
    axes[0].grid(axis="y", alpha=0.2)
    axes[0].tick_params(axis="x", labelrotation=18)

    axes[1].bar(labels, ssim_values, color=colors, width=0.55)
    axes[1].set_title("Edge-loss Ablation: SSIM")
    axes[1].set_ylabel("SSIM")
    axes[1].grid(axis="y", alpha=0.2)
    axes[1].tick_params(axis="x", labelrotation=18)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "edge_ablation_metrics.png", bbox_inches="tight")
    plt.close(fig)


def _best_case_filename() -> str:
    bicubic_rows = {row["filename"]: row for row in read_csv(PROJECT_ROOT / "results" / "bicubic_x2_eval_metrics.csv")}
    imdn_rows = {row["filename"]: row for row in read_csv(_preferred_imdn_metrics_path())}
    scored = []
    for name, bic_row in bicubic_rows.items():
        imdn_row = imdn_rows[name]
        psnr_gain = float(imdn_row["psnr"]) - float(bic_row["psnr"])
        ssim_gain = float(imdn_row["ssim"]) - float(bic_row["ssim"])
        scored.append((psnr_gain + ssim_gain * 10.0, name))
    scored.sort(reverse=True)
    return scored[0][1]


def _failure_case_filename() -> str:
    bicubic_rows = {row["filename"]: row for row in read_csv(PROJECT_ROOT / "results" / "bicubic_x2_eval_metrics.csv")}
    imdn_rows = {row["filename"]: row for row in read_csv(_preferred_imdn_metrics_path())}
    scored = []
    for name, bic_row in bicubic_rows.items():
        imdn_row = imdn_rows[name]
        psnr_gap = float(imdn_row["psnr"]) - float(bic_row["psnr"])
        ssim_gap = float(imdn_row["ssim"]) - float(bic_row["ssim"])
        scored.append((psnr_gap + ssim_gap * 10.0, name))
    scored.sort()
    return scored[0][1]


def _crop_box(image: Image.Image) -> tuple[int, int, int, int]:
    crop_w = min(480, image.width // 2)
    crop_h = min(480, image.height // 2)
    left = max(0, image.width // 2 - crop_w // 2)
    top = max(0, image.height // 2 - crop_h // 2)
    return left, top, left + crop_w, top + crop_h


def _preferred_imdn_metrics_path() -> Path:
    long_path = PROJECT_ROOT / "results_10pt" / "div2k" / "imdn_no_edge_50ep_x2_eval_metrics.csv"
    if long_path.exists():
        return long_path
    return PROJECT_ROOT / "results" / "imdn_x2_no_edge_eval_metrics.csv"


def _preferred_imdn_result_dir() -> Path:
    long_dir = PROJECT_ROOT / "results_10pt" / "div2k" / "imdn_no_edge_50ep_x2_eval"
    if long_dir.exists():
        return long_dir
    return PROJECT_ROOT / "results" / "imdn_x2_no_edge_eval"


def save_visual_comparison(filename: str, output_name: str) -> None:
    paths = {
        "LR Input": PROJECT_ROOT / "data" / "eval" / "LR" / filename,
        "Bicubic": PROJECT_ROOT / "results" / "bicubic_x2_eval" / filename,
        "IMDN 50ep": _preferred_imdn_result_dir() / filename,
        "HR Target": PROJECT_ROOT / "data" / "eval" / "HR" / filename,
    }

    hr_image = Image.open(paths["HR Target"]).convert("RGB")
    box = _crop_box(hr_image)

    panels: list[Image.Image] = []
    for label, path in paths.items():
        image = Image.open(path).convert("RGB")
        if label == "LR Input":
            image = image.resize((hr_image.width, hr_image.height), Image.BICUBIC)
        crop = image.crop(box)
        crop = ImageOps.expand(crop, border=6, fill="white")
        draw = ImageDraw.Draw(crop)
        draw.rectangle((0, 0, crop.width - 1, 32), fill="white")
        draw.text((10, 8), label, fill="black")
        panels.append(crop)

    width = panels[0].width
    height = panels[0].height
    canvas = Image.new("RGB", (width * 2 + 20, height * 2 + 20), color=(245, 243, 238))
    positions = [(0, 0), (width + 20, 0), (0, height + 20), (width + 20, height + 20)]
    for panel, (x, y) in zip(panels, positions):
        canvas.paste(panel, (x, y))

    canvas.save(FIG_DIR / output_name)


def save_full_training_curve_50ep() -> None:
    log_path = PROJECT_ROOT / "logs" / "imdn_x2_no_edge_50ep_metrics.csv"
    if not log_path.exists():
        return
    rows = read_csv(log_path)
    if not rows:
        return
    rows = split_epoch_runs(rows)[-1]
    epochs = [int(row["epoch"]) for row in rows]
    train_loss = [float(row["train_loss"]) for row in rows]
    val_psnr = [float(row["val_psnr"]) for row in rows]
    val_ssim = [float(row["val_ssim"]) for row in rows]
    default_lr = _read_config_learning_rate(PROJECT_ROOT / "src" / "configs" / "imdn_x2_no_edge_50ep.yaml")
    learning_rate = [float(row.get("learning_rate") or default_lr) for row in rows]

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), dpi=200)
    axes[0].plot(epochs, train_loss, color="#a23e2a", linewidth=2)
    axes[0].set_title("IMDN 50ep Training Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].grid(alpha=0.25)
    axes[1].plot(epochs, val_psnr, color="#1d6f8c", linewidth=2, label="PSNR")
    axes[1].plot(epochs, val_ssim, color="#4b8f29", linewidth=2, label="SSIM")
    axes[1].set_title("Validation Metrics")
    axes[1].set_xlabel("Epoch")
    axes[1].grid(alpha=0.25)
    axes[1].legend(frameon=False)
    axes[2].plot(epochs, learning_rate, color="#6b4f8a", linewidth=2)
    axes[2].set_title("Learning Rate (fixed)" if len(set(learning_rate)) == 1 else "Learning Rate")
    axes[2].set_xlabel("Epoch")
    if learning_rate:
        axes[2].set_ylim(0, max(learning_rate) * 1.25)
    axes[2].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    axes[2].grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "full_training_curve_50ep.png", bbox_inches="tight")
    plt.close(fig)


def _read_config_learning_rate(path: Path) -> float:
    if not path.exists():
        return 0.0002
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("learning_rate:"):
            return float(stripped.split(":", 1)[1].strip())
    return 0.0002


def save_dataset_pair_grid() -> None:
    lr_dir = PROJECT_ROOT / "data" / "eval" / "LR"
    hr_dir = PROJECT_ROOT / "data" / "eval" / "HR"
    if not lr_dir.exists() or not hr_dir.exists():
        return
    filenames = [path.name for path in sorted(lr_dir.glob("*.png")) if (hr_dir / path.name).exists()][:4]
    if not filenames:
        return
    cell_width, cell_height = 220, 180
    canvas = Image.new("RGB", (cell_width * len(filenames), cell_height * 2 + 36), color=(247, 246, 242))
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 8), "LR input (bicubic enlarged)", fill="black")
    draw.text((8, cell_height + 26), "HR target", fill="black")
    for index, filename in enumerate(filenames):
        lr_image = Image.open(lr_dir / filename).convert("RGB")
        hr_image = Image.open(hr_dir / filename).convert("RGB")
        lr_image = lr_image.resize(hr_image.size, Image.BICUBIC)
        for row, image in enumerate([lr_image, hr_image]):
            preview = ImageOps.contain(image, (cell_width - 16, cell_height - 24))
            x = index * cell_width + (cell_width - preview.width) // 2
            y = 30 + row * cell_height + (cell_height - 30 - preview.height) // 2
            canvas.paste(preview, (x, y))
    canvas.save(FIG_DIR / "dataset_pair_grid.png")


def save_benchmark_visual_grid() -> None:
    benchmark_root = PROJECT_ROOT / "data" / "benchmarks" / "Set5"
    output_root = PROJECT_ROOT / "results_10pt" / "benchmarks"
    if not output_root.exists():
        output_root = PROJECT_ROOT / "results" / "benchmarks"
    lr_dir = benchmark_root / "LR"
    hr_dir = benchmark_root / "HR"
    bicubic_dir = output_root / "Set5_bicubic_x2"
    imdn_dir = output_root / "Set5_imdn_x2"
    if not all(path.exists() for path in [lr_dir, hr_dir, bicubic_dir, imdn_dir]):
        return
    filename = next((path.name for path in sorted(hr_dir.glob("*.png")) if (imdn_dir / path.name).exists()), "")
    if not filename:
        return
    paths = [
        ("LR Input", lr_dir / filename),
        ("Bicubic", bicubic_dir / filename),
        ("IMDN 50ep", imdn_dir / filename),
        ("HR Target", hr_dir / filename),
    ]
    hr_image = Image.open(hr_dir / filename).convert("RGB")
    box = _crop_box(hr_image)
    panels: list[Image.Image] = []
    for label, path in paths:
        image = Image.open(path).convert("RGB")
        if label == "LR Input":
            image = image.resize(hr_image.size, Image.BICUBIC)
        crop = image.crop(box)
        crop = ImageOps.expand(crop, border=6, fill="white")
        draw = ImageDraw.Draw(crop)
        draw.rectangle((0, 0, crop.width - 1, 32), fill="white")
        draw.text((10, 8), label, fill="black")
        panels.append(crop)
    width = panels[0].width
    height = panels[0].height
    canvas = Image.new("RGB", (width * 4 + 60, height), color=(247, 246, 242))
    for index, panel in enumerate(panels):
        canvas.paste(panel, (index * (width + 20), 0))
    canvas.save(FIG_DIR / "benchmark_visual_grid.png")


def save_perceptual_metric_bar() -> None:
    summary_path = PROJECT_ROOT / "results_10pt" / "perceptual" / "perceptual_summary.csv"
    if not summary_path.exists():
        return
    rows = read_csv(summary_path)
    if not rows:
        return
    methods = [row["method"] for row in rows]
    lpips_values = [float(row["lpips"]) for row in rows]
    niqe_values = [float(row["niqe"]) for row in rows]
    x = np.arange(len(methods))

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), dpi=200)
    axes[0].bar(x, lpips_values, color="#6b8ba4")
    axes[0].set_xticks(x, methods)
    axes[0].set_title("LPIPS (lower is better)")
    axes[0].grid(axis="y", alpha=0.25)
    axes[1].bar(x, niqe_values, color="#b47a46")
    axes[1].set_xticks(x, methods)
    axes[1].set_title("NIQE (lower is better)")
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "perceptual_metric_bar.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    save_training_curve()
    save_full_training_curve_50ep()
    save_metric_bar()
    save_extended_experiment_bar()
    save_capacity_ablation_bar()
    save_scheduler_ablation_bar()
    save_training_time_bar()
    save_ca_imdn_early_stop_analysis()
    save_edge_ablation_bar()
    save_dataset_pair_grid()
    save_benchmark_visual_grid()
    save_perceptual_metric_bar()
    save_visual_comparison(_best_case_filename(), "visual_comparison.png")
    save_visual_comparison(_failure_case_filename(), "visual_comparison_failure.png")


if __name__ == "__main__":
    main()
