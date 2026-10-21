# Design: 项目整顿与模块化

## 核心约束:为什么顺序不能乱

本变更最大的风险不是代码,而是 **Git 状态**。真实运行代码大量未跟踪,因此 **Phase 0(固化基线)必须先于一切**,否则后续任何 git 清理动作都可能不可逆地删除正在运行的程序。

```
Phase 0 固化基线 ──┬── Phase 1 目录瘦身(归档不删) ──┐
   (前置/阻塞)     └── Phase 2 一键运行+降噪 ───────┴── Phase 3 拆分 app.js
                                                          (风险最高,最后做)
```

- Phase 1 与 Phase 2 互相独立,可并行。
- Phase 3 依赖 Phase 0(可回退)+ 自身的烟测前置步骤。

## Phase 0 — 固化 Git 真实基线(前置)

**问题**:`HEAD=73852be` 只含 17 个 java;磁盘 98 个 java + `app.js` 多为未跟踪;另有 29 个删除(其中 18 个 `.planning` 过程稿、11 个旧 `frontend/src` 骨架)。

**决策**:
- 删除(D)按原样提交——它们是被现行实现取代的旧骨架,不恢复。
- 未跟踪(??)的真实源码全部纳入提交。
- 先确认 `.gitignore` 正确忽略 `node_modules/`、`target/`、`dist/`、`out/`、`*.log`、`*.mv.db`、IDE 配置,再 `git add`,避免把构建产物/数据库文件提交进去。
- H2 数据文件(`backend/data/*.mv.db`)**不进仓库**:演示数据由 `DemoSeedService` 启动时自动生成,保持仓库干净且数据可复现。

**验收**:`git status` 干净(除刻意保留的归档目录);`HEAD` 一次 checkout 到干净环境后 `mvn test` + 前端测试仍全绿。

## Phase 1 — 目录瘦身(归档不删)

**策略**:一切先进 `_archive/`,确认无引用后才考虑删除,降低误伤。

| 对象 | 处置 | 理由 |
|---|---|---|
| `课设/新建文件夹/frontend-refactor-example` | 归档 | 另一套废弃 mockup |
| `课设/frontend`(只剩 tests) | 归档 | 残骸,真前端在 `jiaodaluntan/frontend` |
| `课设/openspec`、`.agents`、`.claude`、`agent.md`、`design.md` | 归档 | 游离在真仓库之外 |
| `课设/nul` | 删除 | 误建空文件 |
| `jiaodaluntan/src/Main.java`、`out/` | 归档 | IDE 早期遗留,与 Spring Boot 无关 |
| `frontend/assets/runtime/` | 归档 | 死代码,仅被孤儿测试 `xss-runtime.test.mjs` 引用 |

**注意**:归档 `runtime/` 前需处理 `tests/xss-runtime.test.mjs` 的依赖——要么让该测试改指向拆分后的真实模块,要么一并归档。

## Phase 2 — 一键运行 + 降噪

- **启动脚本(PowerShell)**:检测并清理占用端口的残留进程 → 并行启动后端与前端 → 轮询就绪(探测 `/api/sections`)→ 打印访问地址。
- **端口对齐**:`vite.config.js` 代理目标与后端端口统一,且通过变量/配置可改,不写死。
- **降噪**:评估 lombok/netty 在 Java 高版本下的弃用告警(信息性,可通过日志级别或运行参数收敛);收敛非必要 INFO 噪音。

> 备注:开发期遇到的 `port 8080 already in use`,经实测端口本身可绑定,根因是重复/残留进程抢占。启动脚本的"清端口"步骤即针对此。

## Phase 3 — 拆分 app.js(风险最高,最后做)

**安全网前置**:当前前端测试仅 113 行(2 文件),覆盖薄。45 个函数的重排在此覆盖下属"蒙眼操作"。**拆分前必须先补一层烟测**(关键页面渲染 + 关键交互),作为行为不变的守护。

**拆分粒度(建议)**:
```
frontend/assets/
  app.js              → 仅保留按页面分发的入口
  modules/
    constants.js      路由表 / 存储键 / 常量
    api.js            fetch 封装 / 鉴权头 / 错误处理
    session.js        token/user 状态 + 登录态
    ui.js             escapeHtml / toast / 卡片等 UI 原语
    pages/
      auth.js  home.js  create.js  detail.js  profile.js
      growth.js  rewards.js  admin.js  moderation.js
      users.js  recommendation.js
```

**不可破坏的契约**:
- 各 `code.html` 仍以 `data-page` + `data-*` 属性驱动,拆分只搬运逻辑、不改 DOM 契约。
- 现有 `runtime/` 中已有同名概念(api/session/ui/router),可作为拆分的参考蓝本,但以当前 `app.js` 的真实行为为准。

## Phase 4 — 后端轻整(顺手收尾)

- 合并重复种子服务:`DemoSeedService`(355 行)与 `DemoSeeder`,确认两者职责后保留其一。
- 统一命名与少量去重;**不动**分层架构与 `GlobalExceptionHandler` 异常体系(已规范)。
- 评估 `DemoSeeder`/`LocalDataBootstrapRunner` 的种子入口是否重叠,避免双重灌数据。

## 已决策

- **`_archive/` 纳入 Git(入库)** —— 用户拍板:归档目录随仓库提交留底,而非仅本地留存。
  - 注意:`.gitignore` 中 `out/`、`.idea/`、`node_modules/` 等无锚点规则会误伤 `_archive/` 下的同名子目录,归档入库时需对受影响内容使用 `git add -f` 强制纳入。

## 未决问题 / 待确认
- `docs/` 27 篇报告中,哪些属于"课程要求的正式交付文档",哪些属于过程/自夸记录可归档——需对照课程模板确认。
- 后端启动告警是"收敛"还是"忽略":弃用告警来自三方库,通常不影响功能,优先用日志级别收敛而非改依赖。
