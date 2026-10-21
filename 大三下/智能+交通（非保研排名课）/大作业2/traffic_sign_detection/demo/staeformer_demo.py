"""
STAEformer Traffic Flow Prediction Demo
Loads a pre-trained checkpoint from 大作业1, runs inference on METRLA test set,
and generates visualization plots + metrics JSON for the course report.
"""

import sys
import os
import json
import shutil
from pathlib import Path

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Paths ──────────────────────────────────────────────────────────
HW1_ROOT = Path(r"D:\大三下\智能交通\大作业1")
HW2_ROOT = Path(r"D:\大三下\智能交通\大作业2")

STAE_PKG = HW1_ROOT / "STAEformer_Package"
DATA_DIR = HW1_ROOT / "data" / "METRLA"
CHECKPOINT = HW1_ROOT / "results" / "baseline_METRLA_checkpoint.pth"
RESULTS_YAML = HW1_ROOT / "results" / "baseline_METRLA_results.json"

OUTPUT_DIR = HW2_ROOT / "traffic_sign_detection" / "demo" / "outputs"
REPORT_FIG = HW2_ROOT / "课程设计模版_2026年" / "figures" / "tt100k_experiment"

# ── Import STAEformer from 大作业1 ─────────────────────────────────
sys.path.insert(0, str(STAE_PKG))
from models.base_staeformer import STAEformer
from lib.data_prepare import get_dataloaders_from_index_data
from lib.metrics import RMSE_MAE_MAPE
from lib.utils import StandardScaler, MaskedMAELoss

# ── Config ─────────────────────────────────────────────────────────
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 16


def load_model():
    """Create STAEformer and load pre-trained checkpoint."""
    model_args = dict(
        num_nodes=207, in_steps=12, out_steps=12,
        steps_per_day=288, input_dim=3, output_dim=1,
        input_embedding_dim=24, tod_embedding_dim=24,
        dow_embedding_dim=24, spatial_embedding_dim=0,
        adaptive_embedding_dim=80, feed_forward_dim=256,
        num_heads=4, num_layers=3, dropout=0.1,
    )
    model = STAEformer(**model_args).to(DEVICE)

    ckpt = torch.load(CHECKPOINT, map_location=DEVICE, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    params = sum(p.numel() for p in model.parameters())
    print(f"Model loaded: {params:,} params, best_epoch={ckpt.get('epoch', '?')}")
    return model


def load_data(max_test_samples=500):
    """Load METRLA test dataloader and scaler."""
    tod = True
    dow = True
    data = np.load(DATA_DIR / "data.npz")["data"].astype(np.float32)
    features = [0]
    if tod:
        features.append(1)
    if dow:
        features.append(2)
    data = data[..., features]

    index = np.load(DATA_DIR / "index.npz")
    train_index = index["train"]
    test_index = index["test"]

    from lib.utils import vrange
    x_train_idx = vrange(train_index[:, 0], train_index[:, 1])
    x_test_idx = vrange(test_index[:, 0], test_index[:, 1])
    y_test_idx = vrange(test_index[:, 1], test_index[:, 2])

    x_train = data[x_train_idx]
    x_test = data[x_test_idx]
    y_test = data[y_test_idx][..., :1]

    # Limit test samples for demo speed
    if max_test_samples and len(x_test) > max_test_samples:
        x_test = x_test[:max_test_samples]
        y_test = y_test[:max_test_samples]
        print(f"  Limited to {max_test_samples} test samples")

    scaler = StandardScaler(mean=x_train[..., 0].mean(), std=x_train[..., 0].std())
    x_test[..., 0] = scaler.transform(x_test[..., 0])

    test_loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(
            torch.from_numpy(x_test), torch.from_numpy(y_test)
        ),
        batch_size=BATCH_SIZE, shuffle=False,
    )
    print(f"  Test set: x={x_test.shape}, y={y_test.shape}")
    return test_loader, scaler, y_test


@torch.no_grad()
def run_inference(model, test_loader, scaler):
    """Run inference and collect predictions + ground truth."""
    y_true_list, y_pred_list = [], []
    total = len(test_loader)
    for i, (x_batch, y_batch) in enumerate(test_loader):
        x_batch = x_batch.to(DEVICE)
        out = model(x_batch)
        out = scaler.inverse_transform(out)
        y_pred_list.append(out.cpu().numpy())
        y_true_list.append(y_batch.numpy())
        if (i + 1) % 10 == 0 or (i + 1) == total:
            print(f"  Batch {i+1}/{total}")

    y_true = np.vstack(y_true_list).squeeze()
    y_pred = np.vstack(y_pred_list).squeeze()
    print(f"  Results: y_true={y_true.shape}, y_pred={y_pred.shape}")
    return y_true, y_pred


def compute_metrics(y_true, y_pred):
    """Compute MAE/RMSE/MAPE per step and overall."""
    rmse_all, mae_all, mape_all = RMSE_MAE_MAPE(y_true, y_pred)

    out_steps = y_pred.shape[1] if y_pred.ndim > 2 else 1
    step_results = []
    for s in range(out_steps):
        if y_pred.ndim > 2:
            rmse, mae, mape = RMSE_MAE_MAPE(y_true[:, s, :], y_pred[:, s, :])
        else:
            rmse, mae, mape = RMSE_MAE_MAPE(y_true, y_pred)
        step_results.append({
            "step": s + 1,
            "rmse": float(rmse),
            "mae": float(mae),
            "mape": float(mape),
        })

    metrics = {
        "model": "STAEformer (Baseline)",
        "dataset": "METRLA",
        "overall": {
            "rmse": float(rmse_all),
            "mae": float(mae_all),
            "mape": float(mape_all),
        },
        "per_step": step_results,
    }
    return metrics


def plot_prediction_curve(y_true, y_pred, node_id=42, sample_id=0):
    """Plot prediction vs ground truth for a single node."""
    fig, ax = plt.subplots(figsize=(8, 4))
    steps = range(1, 13)
    ax.plot(steps, y_true[sample_id, :, node_id], "o-", label="Ground Truth", linewidth=2)
    ax.plot(steps, y_pred[sample_id, :, node_id], "s--", label="Prediction", linewidth=2)
    ax.set_xlabel("Prediction Step")
    ax.set_ylabel("Traffic Flow")
    ax.set_title(f"STAEformer Prediction vs Ground Truth (Node {node_id})")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = OUTPUT_DIR / "prediction_curve.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


def plot_step_metrics(metrics):
    """Bar chart of MAE/RMSE per prediction step."""
    steps = [d["step"] for d in metrics["per_step"]]
    mae_vals = [d["mae"] for d in metrics["per_step"]]
    rmse_vals = [d["rmse"] for d in metrics["per_step"]]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(steps))
    w = 0.35
    ax.bar(x - w/2, mae_vals, w, label="MAE", color="#4C72B0")
    ax.bar(x + w/2, rmse_vals, w, label="RMSE", color="#DD8452")
    ax.set_xlabel("Prediction Step")
    ax.set_ylabel("Error")
    ax.set_title("STAEformer: MAE & RMSE per Prediction Step")
    ax.set_xticks(x)
    ax.set_xticklabels(steps)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    path = OUTPUT_DIR / "step_metrics.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


def plot_heatmap(y_true, y_pred, sample_id=0, node_start=0, node_end=20):
    """Heatmap comparison: ground truth vs prediction."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    gt = y_true[sample_id, :, node_start:node_end]
    pr = y_pred[sample_id, :, node_start:node_end]

    vmax = max(gt.max(), pr.max())
    vmin = min(gt.min(), pr.min())

    im0 = axes[0].imshow(gt.T, aspect="auto", cmap="YlOrRd", vmin=vmin, vmax=vmax)
    axes[0].set_title("Ground Truth")
    axes[0].set_xlabel("Prediction Step")
    axes[0].set_ylabel("Node")
    fig.colorbar(im0, ax=axes[0])

    im1 = axes[1].imshow(pr.T, aspect="auto", cmap="YlOrRd", vmin=vmin, vmax=vmax)
    axes[1].set_title("Prediction")
    axes[1].set_xlabel("Prediction Step")
    fig.colorbar(im1, ax=axes[1])

    fig.suptitle("STAEformer: Traffic Flow Heatmap (METRLA)")
    fig.tight_layout()
    path = OUTPUT_DIR / "heatmap_comparison.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


def copy_to_report():
    """Copy generated figures to report directory."""
    REPORT_FIG.mkdir(parents=True, exist_ok=True)
    for f in OUTPUT_DIR.glob("*.png"):
        dst = REPORT_FIG / f"staeformer_{f.name}"
        shutil.copy2(f, dst)
        print(f"  Copied: {dst}")


def main():
    print("=" * 60)
    print("STAEformer Traffic Flow Prediction Demo")
    print("=" * 60)
    print(f"Device: {DEVICE}")

    # 1. Load model
    print("\n[1/5] Loading model...")
    model = load_model()

    # 2. Load data
    print("\n[2/5] Loading METRLA test data...")
    test_loader, scaler, y_test_raw = load_data(max_test_samples=500)

    # 3. Inference
    print("\n[3/5] Running inference...")
    y_true, y_pred = run_inference(model, test_loader, scaler)

    # 4. Metrics
    print("\n[4/5] Computing metrics...")
    metrics = compute_metrics(y_true, y_pred)
    print(f"  Overall: MAE={metrics['overall']['mae']:.4f}, "
          f"RMSE={metrics['overall']['rmse']:.4f}, "
          f"MAPE={metrics['overall']['mape']:.4f}")

    # Save metrics JSON
    metrics_path = OUTPUT_DIR / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"  Saved: {metrics_path}")

    # 5. Visualizations
    print("\n[5/5] Generating visualizations...")
    plot_prediction_curve(y_true, y_pred, node_id=42, sample_id=0)
    plot_step_metrics(metrics)
    plot_heatmap(y_true, y_pred, sample_id=0, node_start=0, node_end=20)

    # 6. Copy to report
    print("\n[6/6] Copying to report directory...")
    copy_to_report()

    print("\n" + "=" * 60)
    print("Done! All outputs in:")
    print(f"  {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
