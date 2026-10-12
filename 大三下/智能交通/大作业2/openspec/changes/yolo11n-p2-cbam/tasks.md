## 1. AutoCBAM 模块实现

- [x] 1.1 创建 `traffic_sign_detection/models/` 目录
- [x] 1.2 编写 `traffic_sign_detection/models/modules.py`，实现 AutoCBAM 包装器类
- [x] 1.3 编写补丁函数 `patch_ultralytics()`，将 AutoCBAM 注入 `ultralytics.nn.tasks` 的 globals
- [x] 1.4 编写单元测试验证 AutoCBAM 通道自动检测和前向传播正确性

## 2. P2+CBAM 模型 YAML

- [x] 2.1 编写 `traffic_sign_detection/models/yolo11n-cbam.yaml`，在 Backbone P2/P3 的 C3k2 后插入 AutoCBAM
- [x] 2.2 编写 `traffic_sign_detection/models/yolo11n-p2.yaml`，添加 P2 检测头（参考 yolov8-p2 模式）
- [x] 2.3 编写 `traffic_sign_detection/models/yolo11n-p2-cbam.yaml`，组合 P2 检测头 + CBAM
- [x] 2.4 验证三个 yaml 均可正常加载并输出正确参数量

## 3. 训练配置与补丁集成

- [x] 3.1 修改 `traffic_sign_detection/train.py`，在模型加载前调用 `patch_ultralytics()`
- [x] 3.2 创建实验配置 `configs/experiments/yolo11n_cbam.yaml`（仅 CBAM，704 输入/50 轮/batch 8）
- [x] 3.3 创建实验配置 `configs/experiments/yolo11n_p2_cbam.yaml`（P2+CBAM，704 输入/50 轮/batch 8）

## 4. 训练与验证

- [ ] 4.1 运行 CBAM 实验：`python train.py --config configs/experiments/yolo11n_cbam.yaml`
- [ ] 4.2 运行 P2+CBAM 实验：`python train.py --config configs/experiments/yolo11n_p2_cbam.yaml`
- [ ] 4.3 收集两组实验的 Precision/Recall/mAP50/mAP50-95 指标
- [ ] 4.4 导出训练曲线、混淆矩阵、预测图到 `figures/tt100k_experiment/`

## 5. 报告更新

- [ ] 5.1 在 `main_report.tex` 的消融实验表中添加 CBAM 和 P2+CBAM 两行结果
- [ ] 5.2 添加 CBAM 和 P2 检测头的原理说明段落
- [ ] 5.3 更新改进方案章节，将 CBAM 和 P2 从"未来工作"改为"已验证改进"
- [ ] 5.4 更新失败案例分析，对比改进前后的检测效果
