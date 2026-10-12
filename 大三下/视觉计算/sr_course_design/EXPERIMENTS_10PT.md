# 10 分冲刺实验矩阵

## 必跑实验

| 实验 | 输入 | 输出 | 用途 |
|---|---|---|---|
| IMDN no-edge 50ep 训练 | `src/configs/imdn_x2_no_edge_50ep.yaml` | `checkpoints/imdn_no_edge_50ep_x2.ckpt`、`checkpoints/imdn_no_edge_50ep_x2_best_psnr.ckpt`、`logs/imdn_x2_no_edge_50ep_metrics.csv` | 解决“5ep 欠训练”和“标准集权重不一致”问题 |
| DIV2K eval | `data/eval/LR`、`data/eval/HR` | `results_10pt/div2k/*_metrics.csv` | 主结果表与 50ep 训练有效性证明 |
| Set5/Set14/BSD100/Urban100 benchmark | `data/benchmarks/<name>` | `results_10pt/benchmarks/benchmark_summary.csv` | 补齐标准 benchmark 评价 |
| LPIPS/NIQE | DIV2K eval 推理结果 | `results_10pt/perceptual/perceptual_summary.csv` | 补齐感知质量指标 |
| 真实图表生成 | 日志、CSV、推理图 | `report/figures/*.png` | 降低 AI 示意图占比，增强图文证据 |

## 预计耗时

实际耗时取决于 CPU 性能和数据规模。按 CPU 环境估算：

| 阶段 | 预计耗时 |
|---|---:|
| smoke 检查 | 1 到 3 分钟 |
| benchmark 下载整理 | 5 到 20 分钟，取决于网络 |
| IMDN 50ep 训练 | 数小时到十余小时 |
| 四个标准集推理评估 | 10 到 60 分钟 |
| LPIPS/NIQE | 10 到 60 分钟 |
| 图表与 PDF 编译 | 1 到 5 分钟 |

## 输出路径

```text
results_10pt/div2k/
results_10pt/benchmarks/
results_10pt/perceptual/
checkpoints/imdn_no_edge_50ep_x2_best_psnr.ckpt
checkpoints/imdn_no_edge_50ep_x2.ckpt
logs/imdn_x2_no_edge_50ep_metrics.csv
report/figures/full_training_curve_50ep.png
report/figures/benchmark_visual_grid.png
report/figures/perceptual_metric_bar.png
report/figures/dataset_pair_grid.png
```

## 优先级

时间不足时优先级如下：

1. IMDN no-edge 50ep 训练和 best checkpoint。
2. Set5、Set14、BSD100、Urban100 benchmark。
3. LPIPS/NIQE。
4. 真实图表与 PDF 编译。
