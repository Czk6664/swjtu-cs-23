# 长训补丁小包安装说明

本补丁包只包含长训配置和一键脚本，不包含数据集、模型权重、推理结果或依赖 wheel。

## 1. 复制位置

将补丁包解压到现有大包根目录，例如：

```text
D:\download\sr_course_design_portabl1e\
```

解压后应得到以下文件位置：

| 小包内文件 | 放到大包哪里 |
|---|---|
| `run_long_training_windows.ps1` | 大包根目录 |
| `src/configs/imdn_x2_no_edge_20ep.yaml` | `src/configs/` |
| `src/configs/imdn_x2_no_edge_50ep.yaml` | `src/configs/` |
| `src/configs/imdn_x2_edge_w001_20ep.yaml` | `src/configs/` |
| `PATCH_INSTALL.md` | 大包根目录，可保留作说明 |

不要移动或删除大包原有的 `data/`、`src/`、`checkpoints/`、`results/`、`vendor/` 等目录。

## 2. 前置条件

先确认原大包环境可用：

```powershell
.\run_smoke_windows.ps1
```

如果还没有安装环境，先运行：

```powershell
.\setup_windows.ps1
```

## 3. 默认长训流程

运行：

```powershell
.\run_long_training_windows.ps1
```

默认会执行：

1. smoke test 和核心 pytest；
2. 训练 `IMDN no-edge 20 epoch`；
3. 训练 `IMDN edge 0.01 20 epoch`；
4. 对两组模型推理完整 100 张 DIV2K 验证图；
5. 生成对应 PSNR/SSIM CSV。

## 4. 跳过测试

如果已经确认环境没问题，可以节省几分钟：

```powershell
.\run_long_training_windows.ps1 -SkipTests
```

## 5. 额外跑 50 epoch

如果要进一步冲高分：

```powershell
.\run_long_training_windows.ps1 -SkipTests -Run50Epoch
```

## 6. 重新生成报告图表

如果希望训练评估后自动重新生成报告图表：

```powershell
.\run_long_training_windows.ps1 -SkipTests -Run50Epoch -RegenerateFigures
```

## 7. 输出文件

默认 20 epoch 输出：

```text
checkpoints/imdn_no_edge_20ep_x2.ckpt
checkpoints/imdn_edge_w001_20ep_x2.ckpt
logs/imdn_x2_no_edge_20ep_metrics.csv
logs/imdn_x2_edge_w001_20ep_metrics.csv
results/imdn_x2_no_edge_20ep_eval/
results/imdn_edge_w001_20ep_x2_eval/
results/imdn_x2_no_edge_20ep_eval_metrics.csv
results/imdn_edge_w001_20ep_x2_eval_metrics.csv
```

开启 `-Run50Epoch` 后额外输出：

```text
checkpoints/imdn_no_edge_50ep_x2.ckpt
logs/imdn_x2_no_edge_50ep_metrics.csv
results/imdn_x2_no_edge_50ep_eval/
results/imdn_x2_no_edge_50ep_eval_metrics.csv
```

## 8. 预计耗时

CPU 环境下大致估计：

- 20 epoch no-edge：40 到 70 分钟；
- 20 epoch edge 0.01：40 到 80 分钟；
- 50 epoch no-edge：1.5 到 2.5 小时；
- 每组完整推理评估：约 7 到 10 分钟。

实际时间取决于目标机器 CPU 和磁盘速度。
