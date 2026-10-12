## ADDED Requirements

### Requirement: AutoCBAM 模块
系统 SHALL 提供 AutoCBAM 包装器模块，该模块在第一次前向传播时自动检测输入通道数并初始化 CBAM，yaml 中不需要硬编码通道数。

#### Scenario: AutoCBAM 自动初始化
- **WHEN** AutoCBAM 模块首次接收输入张量 [B, C, H, W]
- **THEN** 模块 SHALL 自动创建 CBAM(C) 并完成通道+空间注意力计算，输出形状与输入一致 [B, C, H, W]

#### Scenario: AutoCBAM 后续调用
- **WHEN** AutoCBAM 已初始化后再次接收输入
- **THEN** 模块 SHALL 直接使用已初始化的 CBAM 进行计算，不再重新创建

### Requirement: CBAM 插入位置
CBAM SHALL 插入在 Backbone 的 P2 级别（layer 2 C3k2 之后）和 P3 级别（layer 4 C3k2 之后）。P4 和 P5 级别 SHALL NOT 插入 CBAM。

#### Scenario: P2 级别 CBAM
- **WHEN** Backbone P2 C3k2 输出特征
- **THEN** 特征 SHALL 先经过 AutoCBAM 再传入下一层 Conv

#### Scenario: P3 级别 CBAM
- **WHEN** Backbone P3 C3k2 输出特征
- **THEN** 特征 SHALL 先经过 AutoCBAM 再传入下一层 Conv

### Requirement: CBAM 模块兼容性
AutoCBAM SHALL 与 Ultralytics 训练流程完全兼容，支持 model.train()、model.save()、model.load()、model.export()。

#### Scenario: 训练兼容
- **WHEN** 使用包含 AutoCBAM 的模型调用 `model.train()`
- **THEN** 训练 SHALL 正常进行，CBAM 参数参与梯度更新

#### Scenario: checkpoint 保存加载
- **WHEN** 保存并重新加载包含 AutoCBAM 的模型 checkpoint
- **THEN** CBAM 参数 SHALL 完整恢复，推理结果与保存前一致

### Requirement: 模型配置可切换
模型 yaml SHALL 支持通过参数控制是否启用 CBAM 和 P2 检测头，以便进行消融实验。

#### Scenario: 仅启用 CBAM
- **WHEN** 配置 `cbam_enabled=true, p2_enabled=false`
- **THEN** 模型 SHALL 为标准 3 头架构 + Backbone CBAM

#### Scenario: 仅启用 P2
- **WHEN** 配置 `cbam_enabled=false, p2_enabled=true`
- **THEN** 模型 SHALL 为 4 头架构，无 CBAM

#### Scenario: 全部启用
- **WHEN** 配置 `cbam_enabled=true, p2_enabled=true`
- **THEN** 模型 SHALL 为 4 头架构 + Backbone CBAM
