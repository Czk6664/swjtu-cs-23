## ADDED Requirements

### Requirement: 系统必须校验 Windows 项目运行 WSL Hermes 的前置条件
系统必须在启用 Hermes 前校验当前 Windows 环境是否具备通过 WSL 运行 Hermes 的基本条件。

#### Scenario: 环境满足要求
- **WHEN** 应用启动且启用了 WSL Hermes
- **THEN** 系统校验 `wsl.exe` 可用、目标 WSL 发行版存在、Hermes 在 WSL 中可执行，并确认项目路径可映射到 WSL

#### Scenario: 环境不满足要求
- **WHEN** 任一前置条件缺失，例如未安装 WSL、未安装目标发行版或 WSL 中未安装 Hermes
- **THEN** 系统必须返回清晰的初始化错误，并指出具体缺失项

### Requirement: 系统必须提供 Windows 到 WSL 的工作区映射配置
系统必须定义当前项目从 Windows 路径到 WSL 路径的映射规则，并将其用于 Hermes 工作目录和产物目录解析。

#### Scenario: 项目目录位于 D 盘
- **WHEN** 当前项目根目录为 Windows 路径 `D:\...`
- **THEN** 系统能够将其映射为对应的 WSL 路径 `/mnt/d/...`

#### Scenario: 任务需要访问项目状态目录
- **WHEN** Hermes 任务需要读取模板或写入产物
- **THEN** 系统使用映射后的 WSL 路径访问当前项目中的对应目录
