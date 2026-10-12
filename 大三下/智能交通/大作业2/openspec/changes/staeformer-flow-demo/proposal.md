## Why

课程设计高阶要求"综合交通目标识别+交通流量预测，设计构建一套交通态势智能感知分析解决方案"。大作业1 中已有完整的 STAEformer 代码、6 个数据集、以及 baseline/DGL/LA/MST 四种模型的训练 checkpoint 和指标结果。只需写一个推理+可视化脚本，即可在报告高阶部分补充真实的流量预测结果，大幅提升方案说服力。

## What Changes

- 创建 `traffic_sign_detection/demo/` 目录，存放流量预测 demo 脚本和输出
- 编写 `staeformer_demo.py`：加载已训练 checkpoint → 推理 → 可视化预测曲线 → 输出指标
- 从大作业1 复制必要的模型代码和数据路径引用（不复制数据本身，用绝对路径引用）
- 生成 3 张可视化图 + 1 个指标 JSON，用于报告和 PPT

## Capabilities

### New Capabilities
- `flow-prediction-demo`: 加载已训练 STAEformer checkpoint，在 METRLA 测试集上推理并生成预测对比可视化和指标

### Modified Capabilities

（无）

## Impact

- **新增文件**：`traffic_sign_detection/demo/staeformer_demo.py`（~120 行）
- **新增文件**：`traffic_sign_detection/demo/outputs/`（预测曲线图、热力图、指标图、metrics.json）
- **依赖**：复用大作业1 的 STAEformer 模型代码和数据（通过 sys.path 引用）
- **运行时间**：仅推理，不训练，几分钟内完成
- **报告影响**：高阶部分的"模块二：交通流量预测"和"态势融合与决策"将有真实数据支撑
