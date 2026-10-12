# Result Traceability

This file maps reported numeric results to local artifacts so the report can be audited.

## Main DIV2K Validation Results

| Report label | Source CSV | Images | PSNR | SSIM |
|---|---|---:|---:|---:|
| Bicubic | `results/bicubic_x2_eval_metrics.csv` | 100 | 32.4735 | 0.9860 |
| SRCNN | `results/srcnn_x2_eval_metrics.csv` | 100 | 29.0996 | 0.9801 |
| IMDN + Edge Loss (`edge_weight=0.05`) | `results/imdn_x2_eval_metrics.csv` | 100 | 31.1674 | 0.9837 |
| IMDN without Edge Loss | `results/imdn_x2_no_edge_eval_metrics.csv` | 100 | 31.9500 | 0.9855 |

## Quick Fair/Ablation Full-Image Evaluation

| Report label | Source CSV | Images | PSNR | SSIM |
|---|---|---:|---:|---:|
| SRCNN quick | `results/srcnn_fair_quick_x2_eval_metrics.csv` | 100 | 25.3911 | 0.9441 |
| IMDN no-edge quick | `results/imdn_no_edge_fair_quick_x2_eval_metrics.csv` | 100 | 24.2638 | 0.9321 |
| IMDN Edge `0.01` quick | `results/imdn_edge_w001_quick_x2_eval_metrics.csv` | 100 | 24.2792 | 0.9440 |
| IMDN Edge `0.02` quick | `results/imdn_edge_w002_quick_x2_eval_metrics.csv` | 100 | 23.9708 | 0.9314 |

## Quick Training Logs

| Config | Source log |
|---|---|
| `src/configs/srcnn_x2_fair_quick.yaml` | `logs/srcnn_x2_fair_quick_metrics.csv` |
| `src/configs/imdn_x2_no_edge_fair_quick.yaml` | `logs/imdn_x2_no_edge_fair_quick_metrics.csv` |
| `src/configs/imdn_x2_edge_w001_quick.yaml` | `logs/imdn_x2_edge_w001_quick_metrics.csv` |
| `src/configs/imdn_x2_edge_w002_quick.yaml` | `logs/imdn_x2_edge_w002_quick_metrics.csv` |

## Generated Evidence Figures

| Figure | Source |
|---|---|
| `report/figures/training_curves.png` | Latest run split from `logs/imdn_x2_metrics.csv` |
| `report/figures/metric_bar.png` | Main DIV2K validation CSV files |
| `report/figures/edge_ablation_metrics.png` | Main no-edge/edge CSV files and quick edge-weight CSV files |
| `report/figures/visual_comparison.png` | Real LR/Bicubic/IMDN/HR crops selected from CSV comparison |
| `report/figures/visual_comparison_failure.png` | Real failure-case crops selected from CSV comparison |
