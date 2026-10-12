## 1. 环境与配置

- [x] 1.1 在后端设置和 `.env.example` 中增加 WSL Hermes 所需配置项，包括发行版、`wsl.exe` 命令、项目根目录映射和产物目录
- [x] 1.2 实现 WSL Hermes 预检逻辑，检查 `wsl.exe`、目标发行版、WSL 内 Hermes 和项目目录映射
- [x] 1.3 补充 Windows + WSL2 联合运行的基础说明和安装前提

## 2. 路径映射与工作区约束

- [x] 2.1 实现 Windows 路径到 WSL 路径的统一转换工具
- [x] 2.2 为项目根目录、`.task_state` 目录、模板目录和输出目录增加 WSL 映射逻辑
- [x] 2.3 确保所有 Hermes 调用都固定在当前项目对应的 WSL 工作目录中执行

## 3. WSL Hermes 执行适配器

- [x] 3.1 在 `HermesAdapter` 中增加通过 `wsl.exe` 调用 Hermes 的执行链路
- [x] 3.2 记录 WSL Hermes 的标准输出、标准错误、退出状态、超时和产物路径
- [x] 3.3 保留 `HERMES_ENABLED=false` 时的现有兜底执行逻辑

## 4. 任务工作流接入

- [x] 4.1 为 `report` 任务实现 WSL Hermes 的输入初始化和产物回写
- [x] 4.2 为 `voice` 任务实现 WSL Hermes 的输入初始化和产物回写
- [x] 4.3 为 `daily-summary` 任务实现 WSL Hermes 的输入初始化和产物回写
- [x] 4.4 在任务 API 和前端任务中心展示 WSL Hermes 的提供方状态和错误信息

## 5. 验证与文档

- [x] 5.1 添加针对路径映射、WSL 预检和执行失败场景的后端测试
- [ ] 5.2 在本地 Windows + WSL2 环境中验证至少一个 WSL Hermes 任务端到端跑通
- [x] 5.3 在 README 或独立运行文档中补充完整的 Windows 项目 + WSL Hermes 使用说明
