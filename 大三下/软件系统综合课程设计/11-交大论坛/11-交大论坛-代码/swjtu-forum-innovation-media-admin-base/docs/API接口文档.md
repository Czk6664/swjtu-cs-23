# API 接口文档

后端接口统一以 `/api` 为根路径。除公开浏览接口外，受保护接口需要请求头：

```http
Authorization: Bearer <token>
```

统一响应结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## 认证接口

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/auth/register` | 公开 | 注册用户 |
| POST | `/api/auth/login` | 公开 | 登录并返回 JWT |
| GET | `/api/auth/me` | 登录 | 获取当前用户 |

登录请求示例：

```json
{
  "username": "demo_student_anchor",
  "password": "demo-password"
}
```

## 用户接口

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| PUT | `/api/users/me` | 登录 | 更新个人资料 |
| PUT | `/api/users/me/campus-identity` | 登录 | 提交校园身份认证信息 |

## 版块接口

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/sections` | 公开 | 获取版块列表 |

## 帖子与评论接口

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/posts` | 登录 | 发布帖子 |
| GET | `/api/posts` | 公开 | 获取帖子列表 |
| GET | `/api/posts/hot` | 公开 | 获取热门帖子 |
| GET | `/api/posts/search` | 公开 | 搜索帖子 |
| GET | `/api/posts/recommend` | 可选登录 | 获取推荐帖子 |
| GET | `/api/posts/mine` | 登录 | 获取我的帖子 |
| GET | `/api/posts/favorites` | 登录 | 获取我的收藏 |
| GET | `/api/posts/history` | 登录 | 获取浏览记录 |
| GET | `/api/posts/{id}` | 公开 | 获取帖子详情 |
| PUT | `/api/posts/mine/{id}` | 作者 | 编辑自己的帖子 |
| POST | `/api/posts/{id}/like` | 登录 | 点赞帖子 |
| POST | `/api/posts/{id}/favorite` | 登录 | 收藏帖子 |
| POST | `/api/posts/{id}/report` | 登录 | 举报帖子 |
| POST | `/api/posts/{id}/not-interested` | 登录 | 标记不感兴趣 |
| GET | `/api/posts/{id}/comments` | 公开 | 获取评论 |
| POST | `/api/posts/{id}/comments` | 登录 | 发布评论 |
| POST | `/api/posts/comments/{id}/like` | 登录 | 点赞评论 |
| PATCH | `/api/posts/{id}/status` | MODERATOR/ADMIN | 修改帖子状态 |

发帖请求示例：

```json
{
  "title": "课程互助经验分享",
  "content": "这里填写帖子正文",
  "sectionId": 1,
  "tagNames": ["课程互助", "经验贴"]
}
```

## 成长与积分接口

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/growth/interests` | 登录 | 更新兴趣标签 |
| POST | `/api/growth/check-in` | 登录 | 签到 |
| GET | `/api/growth/check-ins` | 登录 | 获取签到记录 |
| GET | `/api/growth/points-history` | 登录 | 获取积分流水 |
| GET | `/api/growth/rewards` | 登录 | 获取奖励列表 |
| POST | `/api/growth/rewards/{id}/redeem` | 登录 | 申请兑换奖励 |
| GET | `/api/growth/redemptions` | 登录 | 获取兑换记录 |

## 后台管理接口

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/admin/posts/pending` | MODERATOR/ADMIN | 待审帖子 |
| GET | `/api/admin/posts` | ADMIN | 全部帖子管理 |
| PUT | `/api/admin/posts/{id}` | ADMIN | 管理员编辑帖子 |
| DELETE | `/api/admin/posts/{id}` | ADMIN | 删除帖子 |
| PATCH | `/api/admin/posts/{id}/status` | MODERATOR/ADMIN | 审核帖子 |
| GET | `/api/admin/reports` | MODERATOR/ADMIN | 举报列表 |
| PATCH | `/api/admin/reports/{id}/review` | MODERATOR/ADMIN | 处理举报 |
| PATCH | `/api/admin/reports/review/bulk` | MODERATOR/ADMIN | 批量处理举报 |
| PATCH | `/api/admin/comments/{id}/hide` | MODERATOR/ADMIN | 隐藏评论 |
| PATCH | `/api/admin/comments/{id}/restore` | MODERATOR/ADMIN | 恢复评论 |
| GET | `/api/admin/users` | ADMIN | 用户列表 |
| PATCH | `/api/admin/users/{id}/ban` | ADMIN | 封禁用户 |
| PATCH | `/api/admin/users/{id}/unban` | ADMIN | 解封用户 |
| POST | `/api/admin/sections` | ADMIN | 新增版块 |
| PUT | `/api/admin/sections/{id}` | ADMIN | 编辑版块 |
| DELETE | `/api/admin/sections/{id}` | ADMIN | 删除版块 |
| GET | `/api/admin/logs` | ADMIN | 操作日志 |
| GET | `/api/admin/redemptions/pending` | ADMIN | 待处理兑换 |
| PATCH | `/api/admin/redemptions/{id}/review` | ADMIN | 审核兑换 |
| GET | `/api/admin/reports/summary` | ADMIN | 举报统计 |
| GET | `/api/admin/recommendations/config` | ADMIN | 获取推荐配置 |
| PUT | `/api/admin/recommendations/config` | ADMIN | 更新推荐配置 |
| GET | `/api/admin/recommendations/preview` | ADMIN | 推荐预览 |

## 常见错误

| 状态 | 含义 | 前端处理 |
|---|---|---|
| 400 | 请求参数校验失败 | 显示字段或表单错误 |
| 401 | 未登录或 Token 失效 | 清除会话并引导登录 |
| 403 | 权限不足 | 显示无权限提示 |
| 404 | 资源不存在 | 显示空状态或返回列表 |
| 500 | 服务端异常 | 显示稍后重试 |

