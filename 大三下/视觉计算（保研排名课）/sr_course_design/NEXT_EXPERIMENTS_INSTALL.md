# 下一轮实验补丁安装说明

本小包用于在已有 20 epoch 结果基础上继续补实验，不包含数据集、模型权重、推理图片或依赖。

## 1. 这次建议跑什么

优先级如下：

1. 必跑：`IMDN no-edge 50 epoch`
   - 目的：证明学习型模型在更充分训练后是否继续提升。
   - 报告价值：形成 `5 epoch -> 20 epoch -> 50 epoch` 的训练充分性曲线。

2. 可选但推荐：`IMDN edge 0.01 50 epoch`
   - 目的：验证 20 epoch 下 edge 0.01 的 SSIM 优势是否稳定。
   - 报告价值：让“改进项实验”不只停留在 20 epoch。

不建议现在跑 edge 0.05 50 epoch，因为 5 epoch 结果已经说明该权重偏强，继续长训的性价比较低。

## 2. 文件放置

将小包解压到现有大包根目录，例如：

```text
D:\download\sr_course_design_portabl1e\
```

解压后应得到：

| 小包内文件 | 放到大包哪里 |
|---|---|
| `run_next_experiments_windows.ps1` | 大包根目录 |
| `src/configs/imdn_x2_no_edge_50ep.yaml` | `src/configs/` |
| `src/configs/imdn_x2_edge_w001_50ep.yaml` | `src/configs/` |
| `NEXT_EXPERIMENTS_INSTALL.md` | 大包根目录 |

## 3. 推荐运行方式

只跑最关键的 no-edge 50 epoch：

```powershell
.\run_next_experiments_windows.ps1 -SkipTests
```

同时跑 no-edge 50 epoch 和 edge 0.01 50 epoch：

```powershell
.\run_next_experiments_windows.ps1 -SkipTests -RunEdge50
```

如果已经有结果，只想生成汇总表：

```powershell
.\run_next_experiments_windows.ps1 -SummarizeOnly
```

如果训练后还想自动刷新报告图：

```powershell
.\run_next_experiments_windows.ps1 -SkipTests -RunEdge50 -RegenerateFigures
```

## 4. 输出文件

no-edge 50 epoch 输出：

```text
checkpoints/imdn_no_edge_50ep_x2.ckpt
logs/imdn_x2_no_edge_50ep_metrics.csv
results/imdn_x2_no_edge_50ep_eval/
results/imdn_x2_no_edge_50ep_eval_metrics.csv
```

edge 0.01 50 epoch 输出：

```text
checkpoints/imdn_edge_w001_50ep_x2.ckpt
logs/imdn_x2_edge_w001_50ep_metrics.csv
results/imdn_edge_w001_50ep_x2_eval/
results/imdn_edge_w001_50ep_x2_eval_metrics.csv
```

自动汇总输出：

```text
results/long_training_summary.csv
results/long_training_summary.md
```

## 5. 发回给我哪些文件

跑完后优先把这些文件或目录给我：

```text
results/long_training_summary.md
results/imdn_x2_no_edge_50ep_eval_metrics.csv
results/imdn_edge_w001_50ep_x2_eval_metrics.csv
logs/imdn_x2_no_edge_50ep_metrics.csv
logs/imdn_x2_edge_w001_50ep_metrics.csv
```

如果没有跑 `-RunEdge50`，就不用发 edge 50 的两个文件。

## 6. 预计耗时

CPU 环境下：

- no-edge 50 epoch：约 1.5 到 2.5 小时；
- edge 0.01 50 epoch：约 1.5 到 2.5 小时；
- 每组推理评估：约 7 到 10 分钟。

如果时间有限，只跑 no-edge 50 epoch 即可。
