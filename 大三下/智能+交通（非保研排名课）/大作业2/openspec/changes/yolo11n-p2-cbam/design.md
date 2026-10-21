## Context

当前 TT100K 交通标志检测实验基于 YOLO11n（2.59M 参数），使用 P3/P4/P5 三个检测头（步长 8/16/32）。数据集分析显示 92% 的目标宽度 < 5% 图像宽度，中位宽度仅约 10 像素。现有三组实验最优 mAP50=0.7580（704 输入/50 轮）。

Ultralytics 8.4.23 已内置 CBAM 模块但未导入 yaml 解析器。官方有 yolov8-p2.yaml 参考架构可移植到 YOLO11。

## Goals / Non-Goals

**Goals:**
- 在 YOLO11n 中添加 P2 检测头（步长 4），专门提升小目标检测能力
- 在 Backbone 中插入 CBAM 注意力，增强特征选择
- 创建 AutoCBAM 包装器，自动适配不同 scale 的通道数
- 保持与现有训练流程（train.py）完全兼容
- 支持三组对比实验：baseline / +CBAM / +P2+CBAM

**Non-Goals:**
- 不修改 Ultralytics 源码
- 不实现 SPD-Conv（与 P2 效果重叠）
- 不修改损失函数或数据增强策略
- 不追求最优超参数（课程设计阶段）

## Decisions

### 决策 1：AutoCBAM 包装器 vs 直接硬编码通道数

**选择**：AutoCBAM 包装器（在第一次前向传播时自动检测通道数）

**理由**：
- CBAM 在 Ultralytics yaml 解析器中不在 `base_modules` 列表，通道数不会被 width 自动缩放
- 硬编码通道数（如 `CBAM, [64]`）只能适配特定 scale，换 scale 就会报错
- AutoCBAM 通过延迟初始化解决此问题，yaml 中写 `AutoCBAM, []` 即可

**替代方案**：修改 Ultralytics `tasks.py` 的 import 列表 → 侵入性太强

### 决策 2：P2 检测头架构设计

**选择**：移植 yolov8-p2.yaml 的模式到 YOLO11

**架构变化**：
```
原架构：Detect(P3/8, P4/16, P5/32)
新架构：Detect(P2/4, P3/8, P4/16, P5/32)
```

**Head 新增路径**：
1. 从 P3（layer 16）Upsample 2x
2. 与 Backbone P2（layer 2, C3k2 输出）Concat
3. C3k2 处理得到 P2 特征
4. 从 P2 下采样，与 P3 Concat，C3k2 精炼 P3
5. Detect 层接收 4 个尺度

**理由**：
- yolov8-p2 是 Ultralytics 官方参考，模式成熟
- P2 层 stride=4，特征图分辨率高，专门保留 10px 级小目标的空间信息
- YOLO11 的 C3k2 替代 YOLOv8 的 C2f，直接替换即可

### 决策 3：CBAM 插入位置

**选择**：在 Backbone 的 P2 和 P3 级别 C3k2 后插入

**理由**：
- P2/P3 是浅层特征，保留了标志的边缘和颜色信息
- CBAM 的通道注意力帮助模型选择最相关的特征通道
- CBAM 的空间注意力帮助模型关注标志所在区域，忽略背景
- 不在 P4/P5 插入，避免计算量过大且深层语义已经足够强

## Risks / Trade-offs

- **[参数量增加]** → P2 检测头增加约 30-50% 参数量。缓解：适当减小 batch size（16→8）
- **[计算量增加]** → P2 层分辨率高，计算量增加。缓解：不在 P4/P5 加 CBAM 控制总量
- **[AutoCBAM 延迟初始化]** → 第一个 batch 才创建 CBAM 参数，checkpoint 保存/加载需确认兼容性。缓解：Ultralytics 的 save/load 处理动态模块
- **[yaml 硬编码问题]** → AutoCBAM 解决了 scale 适配问题，但如果未来需要导出 ONNX 可能需要额外处理

## Open Questions

- P2 检测头是否需要调整 anchor 尺寸？（TT100K 目标普遍很小）
- CBAM 的 kernel_size=7 对于小目标是否过大？可能需要测试 kernel_size=3
