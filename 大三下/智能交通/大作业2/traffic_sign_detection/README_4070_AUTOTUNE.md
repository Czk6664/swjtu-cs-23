# RTX 4070 Laptop Autotune Kit

This kit is designed for unstable laptop GPUs where the goal is to find a stable training setup before running a full TT100K experiment.

## What it does

The script `scripts/autotune_rtx4070.py` runs a short probe sweep on several `(imgsz, batch, workers)` combinations and picks a final config with extra safety margin.

It generates:

- `outputs/autotune_rtx4070/autotune_report.json`
- `outputs/autotune_rtx4070/generated/tt100k_runtime.yaml`
- `outputs/autotune_rtx4070/generated/best_rtx4070.yaml`

## Why this is safer

This search is stability-first:

- probe runs use a very small data fraction
- there is a cooldown between runs
- the script avoids selecting the absolute largest stable batch in `stable` mode
- worker count is tuned separately because unstable laptops often crash from loader pressure or heat, not only VRAM

## Before you run it on the laptop

1. Install Python dependencies.
2. Install a CUDA-enabled PyTorch build that matches your laptop environment.
3. Make sure the TT100K dataset is already prepared in YOLO format.

Expected YOLO dataset layout:

```text
tt100k_yolo/
├─ images/
│  ├─ train/
│  ├─ val/
│  └─ test/
└─ labels/
   ├─ train/
   ├─ val/
   └─ test/
```

## Recommended commands

### 1. Run the autotuner

```powershell
python scripts/autotune_rtx4070.py `
  --dataset-root data\tt100k_yolo `
  --risk-profile stable `
  --probe-epochs 1 `
  --probe-fraction 0.05 `
  --cooldown-seconds 20 `
  --final-epochs 100
```

If the laptop is especially fragile, use:

```powershell
python scripts/autotune_rtx4070.py `
  --dataset-root data\tt100k_yolo `
  --risk-profile stable `
  --probe-epochs 1 `
  --probe-fraction 0.03 `
  --cooldown-seconds 30 `
  --final-epochs 80
```

### 2. Start the full training with the generated config

```powershell
python train.py --config outputs\autotune_rtx4070\generated\best_rtx4070.yaml
```

### 3. Validate with the best weights

Replace the weights path with the actual run folder created by training.

```powershell
python val.py `
  --config outputs\autotune_rtx4070\generated\best_rtx4070.yaml `
  --weights outputs\runs\yolo11n_tt100k_rtx4070_autotuned\weights\best.pt
```

## Files to send back after the laptop run

Please send back these files or folders:

- `outputs/autotune_rtx4070/autotune_report.json`
- `outputs/autotune_rtx4070/generated/best_rtx4070.yaml`
- the full training run directory under `outputs/runs/`
- optionally the final `results.csv`, `results.png`, and `confusion_matrix_normalized.png`

With those results, the experiment can be analyzed and the report can be updated.
