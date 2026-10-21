## Why

当前交大论坛已经具备基础浏览、发帖、评论和后台能力，但作为课程设计展示时，创新性和“真实校园论坛”的产品闭环还不够突出。现在需要在 GitHub 新分支上集中实现 P0/P1 创新功能，让系统从“能发帖”升级为“能解决问题、能体现校园身份、能展示运营价值”的完整校园社区。

## What Changes

- 新增问答采纳能力：楼主可将评论标记为最佳答案，帖子显示“已解决”，并与贡献值、徽章体系联动。
- 新增校园徽章体系：预置校园论坛行为徽章，用户在发帖、评论、签到、被采纳等行为后自动解锁并展示。
- 新增帖子模板能力：发帖时根据版块自动填充课程互助、二手闲置、失物招领等模板，降低发帖成本。
- 新增热门话题榜能力：首页公开展示热门标签、今日热帖和动态热点词云；热点词云使用今日话题拼成 `SWJTU` 字样，增强交大论坛识别度。
- 新增校园身份标签能力：用户可维护兴趣/身份标签，用于个人主页展示和后续推荐扩展。
- 新增校园兴趣圈子能力：提供兴趣圈子列表、加入/退出、圈内帖子等能力；该项作为 P1 后段实现，优先保证主论坛稳定。
- 新增校园数据大屏增强能力：管理后台补充活跃用户、互动数据、趋势统计和运营报告导出，满足课程设计统计分析要求。
- 新增前端动效体验能力：使用 Anime.js 为首页、热榜、词云、卡片进入和状态切换增加流畅动效，依赖必须随前端构建打包，不使用 CDN 或外部本地路径。
- 不引入破坏性接口变更；新增字段、表和接口应兼容现有用户、帖子、评论数据。

## Capabilities

### New Capabilities

- `qa-acceptance`: 支持楼主采纳/取消采纳最佳答案、帖子已解决状态、采纳贡献值和相关展示。
- `campus-badges`: 支持徽章定义、用户徽章授予、行为触发检查、个人主页和帖子详情展示。
- `post-templates`: 支持按版块自动填充发帖模板，帮助用户发布结构化校园帖子。
- `hot-topics`: 支持公开热门标签和今日热帖数据，并在首页侧边栏展示。
- `frontend-motion-experience`: 支持基于 Anime.js 的流畅页面动效和首页 SWJTU 动态热点词云。
- `campus-identity-tags`: 支持用户选择校园身份/兴趣标签，并在个人主页维护和展示。
- `campus-circles`: 支持校园兴趣圈子、成员关系、圈内帖子归属与基础浏览入口。
- `campus-analytics-dashboard`: 支持管理端运营数据大屏增强和报告导出。

### Modified Capabilities

- 无。当前 `openspec/specs` 下没有已登记的能力规范，本次以新增能力为主。

## Impact

- 后端影响：`PostController`、`PostService`、`CommentRepository`、`PostRepository`、`UserController`、`UserService`、`AdminController`、`AnalyticsService`、`LocalDataBootstrapRunner`，并新增徽章、圈子相关实体、仓储、服务和控制器。
- 前端影响：`frontend/assets/modules/pages/detail.js`、`home.js`、`create.js`、`profile.js`、`growth.js`、`admin.js`、`frontend/assets/modules/ui.js`，并新增圈子相关页面。
- 数据库影响：新增 `badges`、`user_badges`、`circles`、`circle_members` 等表；为 `posts`、`comments` 增加兼容字段。
- API 影响：新增采纳、徽章、热门话题、用户标签、圈子、管理统计接口；普通用户接口必须避免误走管理员权限校验。
- 前端依赖影响：新增 `animejs` 作为前端运行时依赖，由 Vite 打包进入 `dist`，不得通过 CDN、绝对本地路径或未纳入项目的外部资源加载。
- 交付影响：建议在 GitHub 分支 `innovation/p0-p1-campus-forum` 上开发，并按 P0 到 P1 小步提交，避免一次性大改导致论坛主流程不可用。
