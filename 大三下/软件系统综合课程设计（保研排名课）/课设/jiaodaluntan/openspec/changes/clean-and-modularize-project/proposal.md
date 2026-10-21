## Why

项目目前“能跑但不可信”：后端编译、启动、`mvn test` 全绿，前端 `app.js` 已把核心功能接通，但工程状态存在三个结构性问题，使它难以交付、难以演示、难以维护。

1. **Git 与真实代码严重脱节**：最后一次提交 `73852be` 只包含 17 个 `.java`（一个早期骨架），而磁盘上真正在运行的有 98 个 `.java` 加 58KB 的 `app.js`，其中 81 个 java、前端运行时几乎全是未跟踪状态（`git status`：120 个 `??`、34 个 `M`、29 个 `D`）。**任何 `git clean/reset/checkout` 都会抹掉真正在跑的程序。**
2. **目录三层嵌套、真假难辨**：真仓库 `jiaodaluntan/` 之外还散落 `新建文件夹/frontend-refactor-example`、只剩 tests 的 `frontend/`、游离的根级 `openspec/`/`.agents/`/`.claude/`、`nul` 空文件；仓库内还有 `src/Main.java`、`out/`、`frontend/assets/runtime/` 等死物。
3. **运行有摩擦**：启动需手动起两个进程，端口 8080 一旦被占就报 `port already in use` 且无自愈；前端代理写死 8080；启动日志噪音多（lombok/netty 弃用告警）。

这次变更的目标是把项目从“能跑”推进到“干净、可一键运行、可信交付”，并把巨型 `app.js` 拆分为可维护模块，同时对后端做轻量收尾——**不改变现有功能行为**。

## What Changes

- **固化 Git 真实基线（前置，最先做）**：将当前可运行的工作树（含全部未跟踪源码与合理删除）整理为提交，使仓库状态与磁盘真实运行代码一致，后续每一步都有可回退 diff。
- **目录瘦身（归档不删）**：把 `jiaodaluntan/` 之外的游离层与仓库内死物迁入 `_archive/`，确认无引用后再清理；删除 `nul` 等明显误建物。保留所有手写文档、课程报告、OpenSpec 资料。
- **一键运行 + 降噪**：提供启动脚本（清理端口占用、并行起前后端、就绪探测）；前端代理目标与后端端口对齐并可配置；压低非必要启动告警与日志噪音。
- **拆分 `app.js`**：在补足烟测安全网后，将 45 个函数按页面/职责拆为 ES Module 模块（路由、会话、API 客户端、各页面控制器、UI 原语），保持外部行为与 `data-*` 契约不变。
- **后端轻整**：合并重复的种子服务（`DemoSeedService` 与 `DemoSeeder`），统一命名与少量去重，不动分层架构与异常处理体系。
- **文档收敛**：保留交付所需文档，归档过程性/自夸类报告，更新 README 的启动说明与目录结构。

## Capabilities

### New Capabilities

- `reproducible-local-startup`: 覆盖“一键、可复现、端口冲突自愈”的本地启动与就绪探测体验，使任意干净环境都能稳定起服并访问。

### Modified Capabilities

- None.（本变更不改变论坛业务行为，仅整顿工程状态、结构与可维护性。）

## Impact

- **Git/仓库**：一次或数次基线整理提交；`.gitignore` 校准；`_archive/` 归档目录；提交历史从此与真实代码一致。
- **目录**：移动/归档 `新建文件夹/`、残骸 `frontend/`、游离 `openspec`/`.agents`/`.claude`、`src/Main.java`、`out/`、`frontend/assets/runtime/`、冗余 `docs/` 报告。
- **前端**：`frontend/assets/app.js` 拆分为 `frontend/assets/modules/*`（或等价结构）；`vite.config.js` 代理配置；新增/扩充前端烟测。
- **后端**：合并 `DemoSeedService`/`DemoSeeder`；少量命名与日志调整；不新增业务接口。
- **运行**：新增启动脚本（PowerShell）；README 启动章节更新。
- **验证**：拆分前先固化烟测基线；拆分后回归同一套烟测，确保行为零变化。
