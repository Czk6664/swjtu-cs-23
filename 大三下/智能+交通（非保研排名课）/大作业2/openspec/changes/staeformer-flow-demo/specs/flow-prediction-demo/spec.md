## ADDED Requirements

### Requirement: 加载已训练 STAEformer checkpoint
系统 SHALL 能够加载大作业1 中已训练的 STAEformer baseline checkpoint（`baseline_METRLA_checkpoint.pth`），并恢复模型权重进行推理。

#### Scenario: checkpoint 加载成功
- **WHEN** 指定 checkpoint 路径和模型配置
- **THEN** 系统 SHALL 加载权重并输出模型参数量确认

### Requirement: METRLA 测试集推理
系统 SHALL 在 METRLA 测试集上运行前向推理，得到预测值和真实值。

#### Scenario: 推理输出形状正确
- **WHEN** 输入测试集数据 (B, 12, 207, 3)
- **THEN** 输出 SHALL 为 (B, 12, 207, 1)，代表 12 步预测

### Requirement: 单节点预测曲线图
系统 SHALL 生成单节点预测 vs 真实的折线图，X 轴为 1-12 预测步，Y 轴为流量值。

#### Scenario: 曲线图生成
- **WHEN** 推理完成
- **THEN** 系统 SHALL 保存 `prediction_curve.png`，包含预测曲线和真实曲线

### Requirement: 逐步指标柱状图
系统 SHALL 生成 1-12 步的 MAE/RMSE 柱状图，展示预测精度随步长的变化。

#### Scenario: 指标图生成
- **WHEN** 推理完成
- **THEN** 系统 SHALL 保存 `step_metrics.png`，包含 12 组 MAE/RMSE 柱状图

### Requirement: 指标 JSON 输出
系统 SHALL 将 MAE/RMSE/MAPE 指标输出到 `metrics.json`。

#### Scenario: JSON 格式正确
- **WHEN** 推理完成
- **THEN** 系统 SHALL 保存 `metrics.json`，包含 overall 和 per_step 两级指标

### Requirement: 结果复制到报告目录
系统 SHALL 将生成的图片复制到 `课程设计模版_2026年/figures/tt100k_experiment/` 目录。

#### Scenario: 文件复制成功
- **WHEN** 可视化生成完成
- **THEN** 图片 SHALL 被复制到报告 figures 目录
