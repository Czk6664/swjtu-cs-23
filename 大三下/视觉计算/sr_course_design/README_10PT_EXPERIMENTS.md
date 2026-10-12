# 10 分冲刺实验增量包使用说明

本增量包用于在另一台机器上补齐课程设计报告的高分实验材料：IMDN 50 epoch 最优 checkpoint、Set5/Set14/BSD100/Urban100 标准集结果、LPIPS/NIQE 感知指标和真实图表。

## 放置位置

将 `sr_10pt_experiment_patch.zip` 解压到原课程项目根目录并覆盖同名文件。项目根目录应包含：

```text
src/
tools/
report/
data/
checkpoints/
logs/
```

不要把补丁包解压到额外的内层目录。

## 运行前检查

确认目标机器有可运行 MindSpore 的 Python 环境，并且数据存在：

```text
data/eval/LR
data/eval/HR
data/LR
data/HR
```

如果标准集尚未准备，脚本会尝试下载 Set5、Set14、BSD100 和 Urban100，并整理为：

```text
data/benchmarks/<Benchmark>/LR
data/benchmarks/<Benchmark>/HR
```

## 推荐命令

先做环境检查：

```powershell
./run_10pt_experiments_windows.ps1 -Stage smoke -Python "你的环境\python.exe"
```

查看完整流程但不真正执行：

```powershell
./run_10pt_experiments_windows.ps1 -DryRun -Python "你的环境\python.exe"
```

正式运行：

```powershell
./run_10pt_experiments_windows.ps1 -Python "你的环境\python.exe"
```

如果目标环境暂时没有 LPIPS/NIQE 依赖，可以先跳过感知指标：

```powershell
./run_10pt_experiments_windows.ps1 -SkipPerceptual -Python "你的环境\python.exe"
```

感知指标依赖安装命令：

```powershell
pip install torch torchvision lpips pyiqa -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 跑完带回

请把以下内容压缩带回原机器：

```text
results_10pt/
checkpoints/imdn_no_edge_50ep_x2_best_psnr.ckpt
checkpoints/imdn_no_edge_50ep_x2.ckpt
logs/imdn_x2_no_edge_50ep_metrics.csv
report/figures/full_training_curve_50ep.png
report/figures/benchmark_visual_grid.png
report/figures/perceptual_metric_bar.png
report/figures/dataset_pair_grid.png
```

其中 `imdn_no_edge_50ep_x2_best_psnr.ckpt` 是优先用于标准集重评和最终报告的权重。
