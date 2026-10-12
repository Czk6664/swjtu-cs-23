## ADDED Requirements

### Requirement: 后端在当前工作区内通过 Hermes 执行任务
当 Hermes 启用时，后端必须通过 Hermes 适配器执行受支持的任务类型，并且所有调用都必须在当前项目工作区内完成。

#### Scenario: 报表任务入队
- **WHEN** 在 Hermes 启用状态下创建一个 `report` 任务
- **THEN** 后端从当前工作区根目录调用 Hermes，并将任务状态从排队中推进到运行中再到终态

#### Scenario: 语音任务入队
- **WHEN** 在 Hermes 启用状态下创建一个 `voice` 任务
- **THEN** 后端在当前工作区内调用与语音播报稿生成对应的 Hermes 工作流

#### Scenario: 每日总结任务入队
- **WHEN** 在 Hermes 启用状态下创建一个 `daily-summary` 任务
- **THEN** 后端在当前工作区内调用与每日总结对应的 Hermes 工作流

### Requirement: 任务结果暴露统一的 Hermes 执行信息
系统必须为 Hermes 任务保存统一的执行结果，包括提供方标识、产物路径以及失败原因。

#### Scenario: Hermes 任务成功
- **WHEN** Hermes 成功完成一个任务
- **THEN** 任务结果中包含 Hermes 提供方标识和稳定的产物引用路径

#### Scenario: Hermes 任务失败
- **WHEN** Hermes 以执行错误、超时或无效输出结束
- **THEN** 任务状态变为失败，并且任务记录中包含可读的失败原因

### Requirement: Hermes 关闭时系统仍可兜底执行
当 `HERMES_ENABLED=false` 时，系统必须保留非 Hermes 的兜底执行路径。

#### Scenario: Hermes 已关闭
- **WHEN** 应用在 `HERMES_ENABLED=false` 下运行
- **THEN** 任务创建仍然成功，系统按照本地 Demo 的兜底逻辑处理任务
