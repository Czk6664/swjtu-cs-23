## ADDED Requirements

### Requirement: WSL Hermes 工作流必须限定在当前项目工作区
系统必须保证通过 WSL 执行的 Hermes 工作流仅在当前项目对应的 WSL 工作区内运行。

#### Scenario: 执行任意 Hermes 任务
- **WHEN** 后端通过 `wsl.exe` 调用 Hermes
- **THEN** Hermes 的工作目录被固定为当前项目在 WSL 中的映射路径

#### Scenario: Hermes 生成任务产物
- **WHEN** Hermes 在 WSL 中生成报表、播报稿或总结文件
- **THEN** 产物被写入当前项目目录中的状态或输出目录，而不是写入任意外部路径

### Requirement: WSL Hermes 必须按任务类型初始化资源
系统必须在执行不同任务前，分别初始化与任务对应的提示词、上下文和输出配置。

#### Scenario: 报表任务执行前初始化
- **WHEN** 一个 `report` 任务准备执行
- **THEN** 系统只准备报表任务所需的模板、输入摘要和输出文件配置

#### Scenario: 语音或每日总结任务执行前初始化
- **WHEN** 一个 `voice` 或 `daily-summary` 任务准备执行
- **THEN** 系统只准备对应任务所需的资源，而不要求其他任务模板已完成初始化

### Requirement: WSL Hermes 产物必须可被 Windows 主系统读取
系统必须保证 WSL Hermes 输出的任务产物能被当前 Windows 主项目直接读取和展示。

#### Scenario: 前端查询已完成任务
- **WHEN** 一个 WSL Hermes 任务完成后，前端查询任务状态或下载产物
- **THEN** 后端返回的产物路径对应当前项目中可访问的文件
