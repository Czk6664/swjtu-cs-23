# 超分辨率课程设计便携包使用说明

## 1. 解压后目录

压缩包包含代码、报告、训练/验证所需数据、已训练 checkpoint、实验日志、评估 CSV 和报告图表。

默认不包含 `data/train_hr_raw`、`data/valid_hr_raw`、`data/valid_lr_raw` 等重复原始目录，因为训练与评估只需要：

- `data/LR`
- `data/HR`
- `data/eval/LR`
- `data/eval/HR`

## 2. 安装依赖

Windows + Conda 环境下，在解压目录执行：

```powershell
.\setup_windows.ps1
```

该脚本会创建 `sr-course-design` 环境，并安装：

- MindSpore 2.8.0
- numpy
- pillow
- pyyaml
- pytest
- matplotlib

如果压缩包内存在 `vendor/wheels`，脚本会优先使用本地 wheel 离线安装依赖；如果不存在，则自动从在线源安装。MindSpore 使用官方 MindSpore / 华为云镜像源。

安装脚本带重试机制。若安装过程中断网或下载失败，恢复网络后重新运行同一条命令即可；已创建的 conda 环境会复用，已存在的本地 wheel 不需要重新下载。

如果要指定环境名：

```powershell
.\setup_windows.ps1 -EnvName mindspore311
```

## 3. 快速验证

```powershell
.\run_smoke_windows.ps1
```

或手动运行：

```powershell
conda run -n sr-course-design python -m src.smoke_test_ms
conda run -n sr-course-design python -m pytest tests/test_losses.py tests/test_models.py tests/test_dataset.py tests/test_infer_smoke.py tests/test_metrics.py -q
```

## 4. 常用命令

一键完成 smoke test、推理、评估和图表生成：

```powershell
.\run_all_windows.ps1 -SkipSetup
```

首次在新机器上使用，可以让脚本先安装/检查环境：

```powershell
.\run_all_windows.ps1
```

如果希望顺便跑快速训练消融：

```powershell
.\run_all_windows.ps1 -SkipSetup -TrainMode quick
```

如果希望重跑主训练流程：

```powershell
.\run_all_windows.ps1 -SkipSetup -TrainMode main
```

如目标机器已安装 TeX Live，并希望同时重新编译报告：

```powershell
.\run_all_windows.ps1 -SkipSetup -CompileReport
```

训练：

```powershell
conda run -n sr-course-design python -m src.train src/configs/imdn_x2_no_edge.yaml
```

推理：

```powershell
conda run -n sr-course-design python -m src.infer --model imdn --scale 2 --num-features 32 --checkpoint ./checkpoints/imdn_no_edge_x2.ckpt --input ./data/eval/LR --output ./results/imdn_x2_no_edge_eval
```

评估：

```powershell
conda run -n sr-course-design python -m src.eval --results ./results/imdn_x2_no_edge_eval --targets ./data/eval/HR --scale 2 --csv ./results/imdn_x2_no_edge_eval_metrics.csv
```

重新生成报告图：

```powershell
conda run -n sr-course-design python tools/generate_report_assets.py
```

## 5. 报告

报告 PDF 位于：

```text
report/main_report.pdf
```

如需重新编译 LaTeX，需要目标机器额外安装 TeX Live / XeLaTeX。
