# CA-IMDN 实验矩阵

## 主实验

| 实验 | 配置 | 目的 |
|---|---|---|
| SRCNN 20ep | `srcnn_x2_20ep.yaml` | 补齐更公平的浅层基线 |
| IMDN 20/50ep | 已有 no-edge 配置 | 主模型长训对照 |
| CA-IMDN 20/50ep | `ca_imdn_x2_no_edge_*.yaml` | 验证通道注意力是否带来收益 |
| CA-IMDN Edge 0.01 20ep | `ca_imdn_x2_edge_w001_20ep.yaml` | 检查注意力与边缘损失是否互补 |

## 消融实验

| 实验 | 配置 | 变量 |
|---|---|---|
| IMDN width16/32/48 | `imdn_x2_width*_20ep.yaml` | 特征通道数 |
| IMDN depth2/4/6 | `imdn_x2_depth*_20ep.yaml` | 蒸馏块数量 |
| IMDN StepLR/CosineLR | `imdn_x2_no_edge_20ep_*_lr.yaml` | 学习率调度 |
| CA-IMDN CosineLR | `ca_imdn_x2_no_edge_20ep_cosine_lr.yaml` | 改进模型调度策略 |

## 预计耗时

实际耗时取决于 CPU、内存和磁盘速度。脚本会在日志中记录每个 epoch 的耗时：

- `epoch_time_sec`
- `learning_rate`

汇总脚本会生成：

- `results/summaries/experiment_summary.csv`
- `results/summaries/experiment_summary.md`
- `results/summaries/parameter_counts.csv`

## 报告使用建议

如果 CA-IMDN 超过 IMDN：

- 结论写作重点：通道注意力增强了信息蒸馏特征的有效通道选择能力。
- 主表中将 CA-IMDN 标为本文最佳自主改进模型。

如果 CA-IMDN 未超过 IMDN：

- 结论写作重点：完整消融证明通道注意力在当前 CPU 轻量配置下收益有限，但比 edge/laplacian 更符合可解释模块化改进。
- 保留负结果，不伪造收益。
