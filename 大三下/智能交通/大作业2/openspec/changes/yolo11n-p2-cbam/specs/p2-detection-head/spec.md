## ADDED Requirements

### Requirement: P2 检测头架构
YOLO11n-P2 模型 SHALL 包含 4 个检测头，分别对应步长 4（P2）、8（P3）、16（P4）、32（P5）。P2 检测头 SHALL 通过从 P3 特征上采样 2x 并与 Backbone P2 层特征拼接实现。

#### Scenario: P2 检测头正确创建
- **WHEN** 加载 `yolo11n-p2-cbam.yaml` 且 `p2_enabled=true`
- **THEN** 模型 SHALL 包含 4 个 Detect 分支，参数量约为 3.5M（比基线增加约 30-50%）

#### Scenario: P2 检测头禁用时回退
- **WHEN** 加载 yaml 且 `p2_enabled=false`
- **THEN** 模型 SHALL 回退到标准 3 头架构（P3/P4/P5），行为与原始 YOLO11n 一致

### Requirement: P2 层通道配置
P2 检测头 C3k2 模块的 yaml 通道数 SHALL 为 256（n-scale 实际通道 64）。P2→P3 下采样 Conv 通道数 SHALL 为 256（n-scale 实际 64）。

#### Scenario: n-scale 通道正确
- **WHEN** 使用 scale=n（width=0.25）加载模型
- **THEN** P2 C3k2 输出通道 SHALL 为 64，P2→P3 Conv 输出通道 SHALL 为 64

### Requirement: Detect 层接收 4 个输入
Detect 层 SHALL 接收来自 P2、P3、P4、P5 四个尺度的特征图。

#### Scenario: Detect 输入正确
- **WHEN** 前向传播时
- **THEN** Detect 层输入 SHALL 为 [P2_features, P3_features, P4_features, P5_features]
