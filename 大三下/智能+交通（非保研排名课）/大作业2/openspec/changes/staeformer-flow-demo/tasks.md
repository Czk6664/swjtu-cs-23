## 1. Demo 脚本编写

- [x] 1.1 创建 `traffic_sign_detection/demo/` 目录和 `outputs/` 子目录
- [x] 1.2 编写 `staeformer_demo.py`：配置路径、导入大作业1 的模型和工具
- [x] 1.3 实现 checkpoint 加载逻辑（创建模型 → 加载 state_dict）
- [x] 1.4 实现 METRLA 测试集数据加载（复用 data_prepare.py）
- [x] 1.5 实现前向推理逻辑（批量推理 → 收集预测值和真实值）

## 2. 可视化生成

- [x] 2.1 实现单节点预测曲线图（prediction_curve.png）
- [x] 2.2 实现多节点热力图对比（heatmap_comparison.png）
- [x] 2.3 实现逐步 MAE/RMSE 柱状图（step_metrics.png）
- [x] 2.4 实现指标 JSON 输出（metrics.json）

## 3. 运行与验证

- [x] 3.1 运行 demo 脚本，确认 3 张图 + JSON 生成成功
- [x] 3.2 将图片复制到 `课程设计模版_2026年/figures/tt100k_experiment/`

## 4. 报告更新

- [x] 4.1 在报告高阶部分的"模块二"插入 STAEformer 预测结果表和图
- [x] 4.2 在"态势融合与决策"部分用真实指标替换示意数据
