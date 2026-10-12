# 10 分冲刺实验检查清单

## 运行前

- [ ] MindSpore 环境可用：`python src/smoke_test_ms.py`
- [ ] `data/LR` 和 `data/HR` 存在，用于训练。
- [ ] `data/eval/LR` 和 `data/eval/HR` 存在，用于验证与主结果。
- [ ] PowerShell 当前目录是项目根目录。

## 运行命令

- [ ] 已执行 smoke：`./run_10pt_experiments_windows.ps1 -Stage smoke -Python "你的环境\python.exe"`
- [ ] 已执行正式流程：`./run_10pt_experiments_windows.ps1 -Python "你的环境\python.exe"`

## 训练输出

- [ ] `checkpoints/imdn_no_edge_50ep_x2.ckpt`
- [ ] `checkpoints/imdn_no_edge_50ep_x2_best_psnr.ckpt`
- [ ] `logs/imdn_x2_no_edge_50ep_metrics.csv`
- [ ] 日志 CSV 至少包含 50 个 epoch 的记录。

## 标准集输出

- [ ] `results_10pt/benchmarks/benchmark_summary.csv`
- [ ] `results_10pt/benchmarks/benchmark_summary.md`
- [ ] Set5、Set14、BSD100、Urban100 至少各有 Bicubic 和 IMDN 的 metrics CSV。

## 感知指标输出

- [ ] `results_10pt/perceptual/perceptual_metrics.csv`
- [ ] `results_10pt/perceptual/perceptual_summary.csv`
- [ ] summary 中至少包含 Bicubic 和 IMDN50 两行。

## 真实图表输出

- [ ] `report/figures/full_training_curve_50ep.png`
- [ ] `report/figures/benchmark_visual_grid.png`
- [ ] `report/figures/perceptual_metric_bar.png`
- [ ] `report/figures/dataset_pair_grid.png`

## 带回原机器

- [ ] `results_10pt/`
- [ ] `checkpoints/imdn_no_edge_50ep_x2_best_psnr.ckpt`
- [ ] `checkpoints/imdn_no_edge_50ep_x2.ckpt`
- [ ] `logs/imdn_x2_no_edge_50ep_metrics.csv`
- [ ] 新生成的 `report/figures/*.png`
