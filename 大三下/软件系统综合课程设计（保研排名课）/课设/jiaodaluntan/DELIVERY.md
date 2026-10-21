# 西南交大校园论坛交付说明

## 交付内容

- `backend/`：Spring Boot 后端源码，包含认证、帖子、评论、关注、通知、成长积分、举报治理和后台统计。
- `frontend/`：Vite 多页面前端源码，所有页面通过 `frontend/assets/app.js` 统一接入真实接口。
- `docs/`：API、数据库、系统设计、安全审计、启动配置和交付边界说明。
- `start.ps1`：源码目录一键启动脚本，会自动构建缺失的后端 jar 和前端 `dist`。
- `packaging/`：便携交付包构建材料，包含静态前端服务器和 portable 启停脚本。
- `release/`：生成后的交付包输出目录，不属于源码主线。

## 一键启动

在项目根目录运行：

```powershell
.\start.ps1
```

默认访问地址：

- 前端页面：`http://localhost:4173`
- 后端接口：`http://localhost:8080/api`
- H2 控制台：`http://localhost:8080/api/h2-console`

默认管理员：

- 用户名：`admin`
- 密码：`admin123456`

## 手动验证

后端测试：

```powershell
cd backend
mvn test
```

前端测试与构建：

```powershell
cd frontend
npm test
npm run build
```

## 交付边界

- `backend/target/`、`frontend/dist/`、`release/`、`_shots/`、日志文件和压缩包都是生成物，不作为核心源码评审对象。
- 默认本地模式使用 H2 文件数据库，适合答辩演示；如需 MySQL，可参考 `README.md` 和 `docs/启动与配置说明.md`。
- 演示账号仅用于课程设计本地展示，正式部署应更换 `JWT_SECRET` 和默认管理员密码。
