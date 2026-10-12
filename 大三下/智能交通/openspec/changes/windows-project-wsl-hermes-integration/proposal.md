## 为什么

当前项目运行在 Windows 工作区中，但 Hermes Agent 官方要求通过 WSL2 运行，无法直接作为原生 Windows 组件接入。为了在不迁移整个项目开发环境的前提下使用 Hermes，需要建立一套“Windows 项目 + WSL Hermes”的稳定接入方案，让现有前后端继续运行在 Windows 环境中，同时把 Hermes 作为 WSL 内的任务执行层纳入项目。

## 变更内容

- 建立 Windows 项目调用 WSL 中 Hermes 的统一接入方案。
- 定义 Windows 路径与 WSL 路径之间的映射规则，使 Hermes 能固定在当前项目工作区内运行。
- 增加后端到 `wsl.exe` 的调用适配层，用于在 WSL 中启动 Hermes 并收集结果。
- 设计 Hermes 在 WSL 中的初始化、安装校验、工作目录约束和任务执行约束。
- 规范报表、播报稿和每日总结任务如何通过 WSL Hermes 执行并把产物回写到当前项目目录。
- 补充 Windows + WSL 联合运行的启动说明、故障排查和验证步骤。

## 能力

### 新增能力
- `windows-wsl-hermes-bootstrap`: 为当前 Windows 项目建立 WSL Hermes 安装检查、工作区映射和启动校验能力。
- `windows-to-wsl-hermes-execution`: 支持后端通过 `wsl.exe` 在 WSL 内执行 Hermes 任务，并将结果回写到 Windows 项目目录。
- `workspace-scoped-wsl-hermes-workflows`: 定义仅在当前项目工作区内运行的 WSL Hermes 工作流，用于报表、播报稿和每日总结任务。

### 修改能力

无。

## 影响范围

- 受影响代码：`services/api/app/services/hermes.py`、后端任务执行链路、配置模块、启动脚本和运行文档。
- 受影响接口：`/api/tasks`、`/api/tasks/{task_id}` 以及所有触发 Hermes 后台任务的入口。
- 新增依赖或系统：WSL2、WSL 内安装的 Hermes、Windows 到 WSL 的路径映射逻辑、基于 `wsl.exe` 的调用方式和工作区内产物目录。
