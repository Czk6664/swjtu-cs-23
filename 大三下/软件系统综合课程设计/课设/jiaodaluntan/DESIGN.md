# 西南交大校园论坛设计说明

## 1. 架构概览

系统采用前后端分离的 B/S 架构。前端是 Vite 多页面应用，后端是 Spring Boot 分层服务，MySQL 保存核心业务数据，Redis 作为缓存和短期状态扩展点。

```text
Browser
  |
  | HTML/CSS/JS + /api requests
  v
Vite MPA frontend
  |
  | proxy /api
  v
Spring Boot backend
  |
  +-- Controller
  +-- Service
  +-- Repository
  |
  +-- MySQL
  +-- Redis
```

## 2. 前端 MPA 设计

前端保留多页面应用结构，每个业务页面都有独立 HTML shell，例如首页、帖子详情、个人中心、成长中心、管理页等。页面通过 `data-page` 标识当前业务入口，通过 `data-slot` 暴露可被运行时替换的内容区域。

选择 MPA 的原因：

- 课程项目页面数量固定，MPA 结构直观，便于答辩展示。
- 每个页面可以直接打开和检查，降低部署复杂度。
- 共享运行时统一处理 API、登录状态、错误提示和动态渲染。

核心约束：

- HTML shell 保留 `data-page` 和 `data-slot` 合同。
- 页面内容可以动态接入真实接口，但结构入口保持稳定。
- 构建仍由 `frontend/vite.config.js` 的多入口配置统一管理。

## 3. 后端分层设计

后端采用 Spring Boot 常见分层：

| 层级 | 责任 |
|---|---|
| Controller | 接收 HTTP 请求，进行参数校验，返回统一 `ApiResponse` |
| Service | 执行业务规则、权限边界、积分变动、审核流程 |
| Repository | 使用 Spring Data JPA 访问数据库 |
| Entity/DTO | 分离数据库实体和接口请求对象 |
| Security | JWT 解析、登录状态注入、角色鉴权 |

后端接口统一挂载在 `/api` 下。公开读取接口允许游客访问，写操作和后台操作通过 JWT 和角色权限控制。

## 4. 认证与权限

系统使用 JWT Bearer Token。登录成功后前端保存 token，后续请求通过 `Authorization: Bearer <token>` 传递身份。

权限分为：

| 角色 | 权限 |
|---|---|
| 游客 | 浏览公开版块、公开帖子、帖子详情 |
| USER | 发帖、评论、点赞、收藏、签到、兑换 |
| MODERATOR | 内容治理、举报处理、帖子状态审核 |
| ADMIN | 用户管理、版块管理、推荐策略、后台总览、全部治理能力 |

后台接口使用 `@PreAuthorize` 保护，前端也会进行页面级和操作级提示，但最终权限以后端判断为准。

## 5. 数据库设计

数据库名为 `swjtu_forum`，主要实体包括：

- `users`
- `sections`
- `posts`
- `comments`
- `tags`
- `post_likes`
- `post_favorites`
- `post_browse_history`
- `reports`
- `points_history`
- `reward_items`
- `redemption_requests`
- `recommendation_configs`

帖子、评论、点赞、收藏等表通过外键关联用户和帖子。点赞收藏等操作使用唯一约束防止重复写入。

## 6. 安全设计

### SQL 注入防护

当前仓库查询使用 Spring Data JPA 方法名查询和 JPQL 参数绑定，例如 `@Param("keyword")`，没有通过字符串拼接生成 SQL。实现阶段如果发现 `nativeQuery` 或字符串拼接 SQL，必须改为参数化查询。

### XSS 防护

前端将后端返回的所有文本视为不可信数据。动态文本必须满足以下规则之一：

- 使用 DOM API 和 `textContent` 写入。
- 使用统一 HTML 转义函数后再进入模板字符串。
- 属性值只使用受控枚举、数字 ID 或经过转义的值。

动态渲染点需要通过恶意字符串测试覆盖，重点包括帖子标题、正文、评论、用户名、举报原因、奖励描述和推荐预览内容。

### 输入验证

后端 DTO 使用 `@NotBlank`、`@Size`、`@Email`、`@Pattern`、`@Min`、`@Max` 等 Bean Validation 注解。Controller 使用 `@Valid` 触发校验。

## 7. API 设计

接口采用 JSON，请求成功时返回统一 `ApiResponse`：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

接口清单见 [docs/API接口文档.md](docs/API接口文档.md)。

## 8. 测试与验证

验证分为四类：

- 前端构建：`npm run build`
- 前端页面和运行时测试：`node tests/phase06-plan01.test.mjs`
- 后端单元/契约测试：`mvn test`
- 真实数据 smoke test：启动 MySQL、Redis、demo profile 后验证游客、普通用户、管理员链路

验证矩阵见 [docs/质量验证矩阵.md](docs/质量验证矩阵.md)。

## 9. 主要取舍

| 选择 | 原因 |
|---|---|
| 保留 Vite MPA | 更适合课程展示，页面入口清晰 |
| 不临时迁移到前端框架 | 避免为了重构引入更大风险 |
| 先补 Markdown API 文档 | 对评审最直接，低风险 |
| 保留 MySQL + Redis | 与现有后端和课程要求一致 |

