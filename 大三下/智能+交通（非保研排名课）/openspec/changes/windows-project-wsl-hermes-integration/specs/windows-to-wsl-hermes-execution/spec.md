## ADDED Requirements

### Requirement: 后端必须通过 wsl.exe 调用 WSL 中的 Hermes
当 Hermes 启用时，后端必须通过 `wsl.exe` 在目标 WSL 发行版中调用 Hermes，而不是尝试在原生 Windows 运行时中直接执行 Hermes。

#### Scenario: 创建报表任务
- **WHEN** 后端收到一个 `report` 类型任务
- **THEN** 系统通过 `wsl.exe` 在目标 WSL 发行版内执行对应的 Hermes 命令

#### Scenario: 创建语音或每日总结任务
- **WHEN** 后端收到一个 `voice` 或 `daily-summary` 任务
- **THEN** 系统通过 `wsl.exe` 在目标 WSL 发行版内执行对应的 Hermes 命令

### Requirement: 后端必须记录 WSL Hermes 执行结果
系统必须记录通过 WSL Hermes 执行任务时的结果信息，包括提供方、标准输出、标准错误、退出状态和产物路径。

#### Scenario: WSL Hermes 成功完成任务
- **WHEN** Hermes 在 WSL 中成功执行完成
- **THEN** 任务记录中包含成功状态、执行提供方和产物引用

#### Scenario: WSL Hermes 执行失败
- **WHEN** `wsl.exe` 调用失败、Hermes 返回错误或任务超时
- **THEN** 任务记录中包含失败状态和可读的错误原因

### Requirement: 系统必须保留非 Hermes 兜底路径
当 WSL Hermes 不可用或被禁用时，系统必须保留当前已有的兜底执行路径。

#### Scenario: WSL Hermes 被关闭
- **WHEN** `HERMES_ENABLED=false`
- **THEN** 系统继续使用非 Hermes 的任务执行逻辑，且任务接口仍然可用
