# CA-IMDN 实验补强增量包说明

本补丁包用于在已有 `sr_course_design` 项目或便携大包上增量加入 CA-IMDN、学习率策略、耗时统计、频域分析和大规模实验矩阵。补丁包不包含 DIV2K 原始数据和 Conda 环境。

## 放置方式

将补丁包解压后，把 `code_patch/` 内文件按原相对路径复制到项目根目录。例如：

- `code_patch/src/models/imdn.py` 覆盖到 `src/models/imdn.py`
- `code_patch/src/train.py` 覆盖到 `src/train.py`
- `code_patch/src/infer.py` 覆盖到 `src/infer.py`
- `code_patch/src/configs/*.yaml` 复制到 `src/configs/`
- `code_patch/tools/*.py` 复制到 `tools/`
- `scripts/run_ca_experiments_windows.ps1` 复制到项目根目录

`report_patch/` 中包含当前报告源文件、PDF 和新增图表，可按需覆盖到 `report/`。

## 一键运行

在项目根目录执行：

```powershell
.\run_ca_experiments_windows.ps1 -Python D:\Anaconda_envs\envs\mindspore311\python.exe
```

只检查命令和路径，不实际训练：

```powershell
.\run_ca_experiments_windows.ps1 -DryRun
```

只跑最小 CA-IMDN smoke 矩阵：

```powershell
.\run_ca_experiments_windows.ps1 -Stage smoke
```

## 输出位置

- checkpoint：`checkpoints/`
- 训练日志：`logs/`
- 推理图像：`results/<model>_x2_eval/`
- 指标 CSV：`results/<model>_x2_eval_metrics.csv`
- 汇总表：`results/summaries/`
- 频域图：`report/figures/frequency_analysis.png`

## Benchmark 数据

标准 benchmark 是可选项。若存在以下目录，一键脚本会自动评估：

```text
data/benchmarks/Set5/LR
data/benchmarks/Set5/HR
data/benchmarks/Set14/LR
data/benchmarks/Set14/HR
data/benchmarks/BSD100/LR
data/benchmarks/BSD100/HR
data/benchmarks/Urban100/LR
data/benchmarks/Urban100/HR
```

如果没有这些目录，benchmark 步骤会自动跳过。
