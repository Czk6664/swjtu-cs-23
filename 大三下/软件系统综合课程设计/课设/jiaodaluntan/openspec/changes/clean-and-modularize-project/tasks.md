## 0. 固化 Git 真实基线(前置 — 必须最先完成)

- [x] 0.1 备份当前工作树(`_jiaodaluntan_backup_20260524/`,345 文件含未跟踪源码,排除 node_modules/target/dist/out/.git)
- [x] 0.2 校准 `.gitignore`:补充 `*.iml/*.ipr/*.iws`、`.settings/`;确认已忽略 node_modules/target/dist/out/data(*.mv.db)/logs/IDE
- [x] 0.3 复核 `git status`:确认无已跟踪垃圾、未跟踪无产物/数据库混入,删除均为旧骨架(frontend/src + .planning 过程稿)
- [x] 0.4 分三次提交:cc98a6d 后端源码、b1fe807 前端运行时、849eec9 文档/规划/openspec
- [x] 0.5 验证:全新 worktree 检出含全部关键源码,`mvn test-compile` 通过(exit=0)
- [x] 0.6 确认 `git status` 干净;跟踪文件 88 → 314

## 1. 目录瘦身(归档不删 — 依赖 Phase 0)

- [x] 1.1 建立 `_archive/`,决定纳入 Git(`git add -f`,因 out/ 等被 ignore);412K/79 文件,无 node_modules
- [x] 1.2 归档外层游离物 → `_archive/课设-strays/`(新建文件夹、frontend 残骸、openspec、.agents、.claude、agent.md、design.md)
- [x] 1.3 删除 `课设/nul`(Windows 保留名,用 `\\?\` 扩展路径删除)
- [x] 1.4 归档仓库内死物 → `_archive/repo-dead/`(src/Main.java、out/);提交 5adb319
- [x] 1.5 `frontend/assets/runtime/` 已随 Phase 3 归档到 `_archive/repo-dead/frontend-runtime/`,应用与测试引用清零
- [x] 1.6 归档后 `git status` 干净,无引用断裂(runtime/ 未动,xss 测试仍可跑)

## 2. 一键运行 + 降噪(依赖 Phase 0,可与 Phase 1 并行)

- [x] 2.1 `start.ps1`:`Clear-Port` 检测占用 8080/5173 的 java/node 残留并 `Stop-Process`,空闲不报错
- [x] 2.2 `start.ps1`:`Start-Process` 并行拉起后端与前端(前端无 node_modules 时先 npm install)
- [x] 2.3 `start.ps1`:`Wait-BackendReady` 轮询 `/api/sections`=200(超时 120s)后打印访问地址 + admin 账号
- [x] 2.4 `vite.config.js`:target 改为 `http://localhost:${BACKEND_PORT||8080}`,其余 MPA 配置不变
- [x] 2.5 降噪:application.yml 把 Hikari/Hibernate/H2 启动期 INFO 收敛到 WARN(env 可覆盖);lombok/netty 告警来自 JVM 层无法 yml 收敛
- [x] 2.6 README:新增「一键启动」章节 + 目录结构表(标注 _archive 为归档、真实代码在 backend/frontend);提交 75a25fd

## 3. 拆分 app.js(风险最高 — 依赖 Phase 0 + 本阶段烟测前置)

- [~] 3.1 安全网:**未新建独立 Playwright 套件**;改用「`npm run build` 全 14 入口 + 现有 phase06/xss 测试 + 逐字搬运纪律」作为行为守护,运行时行为由 5.1 手动烟测兜底
- [x] 3.2 拆分前确认基线全绿(build + 两测试),作为对照
- [x] 3.3 抽离基础层:`modules/constants.js`、`api.js`、`session.js`、`ui.js`(共享态 state/sectionsCache 各仅一份)
- [x] 3.4 11 个页面控制器抽到 `modules/pages/*.js`(auth/home/create/detail/profile/growth/rewards/admin/moderation/users/recommendation)
- [x] 3.5 `app.js` 收敛为 64 行入口:按 `data-page` 分发 + 全局导航/popstate 接线
- [x] 3.6 未改任何 `code.html` 标记;`data-*` 契约不变(逐字搬运函数体)
- [x] 3.7 回归:`npm run build` 成功(bundle 43KB/gzip 12.4KB)、phase06+xss 全绿
- [x] 3.8 修正测试失真:xss 改指 `modules/ui.js`;phase06 改读 `assets/modules/`(原读已废 runtime),并**删除 agent 为过测试在 app.js 塞的注释 token hack**——测试现在校验真实模块,死断言 `renderHomeLayout` 换成真实 `renderHome`

## 4. 后端轻整(顺手收尾 — 依赖 Phase 0)

- [x] 4.1 调研结论:本地默认启动走 `LocalDataBootstrapRunner`(admin+7生产版块);`demo` profile 走 `DemoSeedRunner→DemoSeedService`(demo_*锚点+3演示版块)。两路径数据零重叠,默认启动只跑一条,**无双重灌数据**
- [x] 4.2 判定**无需合并**:`DemoSeeder` 接口是有意解耦(runner→interface→service,便于测试 mock),非冗余;强行合并会破坏两套 guard 语义、改变业务行为,违反轻整原则
- [x] 4.3 命名风格已一致(均 `ensureXxx` 幂等模式);唯一小重复 `ensureSection/ensureTag` 服务于不同数据集与事务边界,抽公共类收益<风险,不在范围内
- [x] 4.4 `mvn -o test`(DemoSeedServiceTest、DemoSeedRunnerTest)全绿,仅 JDK25 无害告警

## 5. 收尾验收

- [x] 5.1 全栈运行时烟测:8080+5173 拉起就绪;后端全链路 API(登录→版块→发帖→点赞→评论→签到→后台用户→详情,详情 likes=1/comments=1 计数正确);Vite 转译并服务全部 8 个核心模块 200。注:Playwright 浏览器桥未装,以 API 级 + 模块加载验证替代点击式烟测
- [x] 5.2 全量回归:后端 `mvn test` 全绿(DONE_0)、前端 phase06+xss 全绿、`npm run build` 14 入口成功
- [x] 5.3 `git status` 干净,跟踪文件 88→314,7 次基线/整顿提交与真实代码一致
- [x] 5.4 README 新增一键启动+目录表;CLAUDE.md 修正零配置 H2 启动事实;docs 分流为交付档+归档
