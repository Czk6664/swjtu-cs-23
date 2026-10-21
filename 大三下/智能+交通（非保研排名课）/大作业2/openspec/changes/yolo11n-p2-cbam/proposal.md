## Why

TT100K 数据集中 92% 的交通标志目标宽度不到图像的 5%，中位宽度仅约 10 像素（@640）。当前 YOLO11n 基线使用 P3/P4/P5 三个检测头（步长 8/16/32），对极小目标的特征保留不足，mAP50 仅 0.7580。需要通过结构改进提升小目标检测能力。

## What Changes

- 在 YOLO11n 的 Neck 中新增 P2 检测头（步长 4），专门检测远距离小尺寸交通标志
- 在 Backbone 的 C3k2 模块后插入 CBAM（通道+空间注意力），增强特征选择能力
- 创建 AutoCBAM 包装器模块，自动适配不同 scale 的通道数，避免硬编码
- 新建自定义模型 yaml 文件 `yolo11n-p2-cbam.yaml`，不修改 Ultralytics 源码
- 新建实验配置文件，支持三组对比实验（baseline / +CBAM / +P2+CBAM）

## Capabilities

### New Capabilities
- `p2-detection-head`: 在 YOLO11n 中添加步长为 4 的 P2 检测头，将检测尺度从 3 个扩展到 4 个
- `cbam-attention`: 在 Backbone 中插入 CBAM 注意力模块，包含 AutoCBAM 自动通道适配包装器

### Modified Capabilities

（无已有 spec 需要修改）

## Impact

- **新增文件**：`traffic_sign_detection/models/yolo11n-p2-cbam.yaml`（自定义模型架构）
- **新增文件**：`traffic_sign_detection/models/modules.py`（AutoCBAM 包装器）
- **新增文件**：`traffic_sign_detection/configs/experiments/yolo11n_cbam.yaml`、`yolo11n_p2_cbam.yaml`（实验配置）
- **依赖**：无新依赖，CBAM 已内置于 Ultralytics 8.4.23
- **训练资源**：P2 检测头增加约 30-50% 参数量，需适当减小 batch size
