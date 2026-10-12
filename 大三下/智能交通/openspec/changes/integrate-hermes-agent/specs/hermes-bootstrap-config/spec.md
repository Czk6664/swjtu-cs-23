## ADDED Requirements

### Requirement: 启用 Hermes 前校验工作区本地运行环境
系统必须在启用 Hermes 任务执行前，校验 Hermes 运行时是否可用，以及项目工作区内的配置是否完整。

#### Scenario: Hermes 已启用且运行环境可用
- **WHEN** 应用以 `HERMES_ENABLED=true` 启动，且配置的 Hermes 命令可用
- **THEN** 系统完成命令、输出目录、工作区状态目录和运行配置校验，并正常启动

#### Scenario: Hermes 已启用但运行环境不可用
- **WHEN** 应用以 `HERMES_ENABLED=true` 启动，但 Hermes 命令无法解析或执行
- **THEN** 系统必须暴露清晰的配置错误，指出 Hermes 初始化失败

### Requirement: 提供明确的工作区本地 Hermes 配置
系统必须定义项目级 Hermes 配置，包括命令解析、超时、工作区上下文、状态目录和输出位置。

#### Scenario: 开发者准备本地环境
- **WHEN** 开发者查看环境变量模板或运行文档
- **THEN** 文档明确列出 Hermes 配置项、工作区内目录和本地初始化步骤

#### Scenario: Hermes 任务生成产物
- **WHEN** 一个 Hermes 任务成功完成
- **THEN** 系统把产物写入配置指定的项目内目录

### Requirement: Hermes 按任务类型准备初始化资源
系统必须在当前工作区内按任务类型分别准备 Hermes 初始化资源。

#### Scenario: 报表任务启动
- **WHEN** 一个报表任务准备通过 Hermes 执行
- **THEN** 系统只创建或解析该报表任务所需的提示词、载荷和输出配置

#### Scenario: 语音或每日总结任务启动
- **WHEN** 一个语音任务或每日总结任务准备通过 Hermes 执行
- **THEN** 系统只初始化对应任务类型所需资源，而不要求其他任务模板提前准备完成
