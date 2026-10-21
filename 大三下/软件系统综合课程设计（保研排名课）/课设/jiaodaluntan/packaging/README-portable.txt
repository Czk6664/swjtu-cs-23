西南交大论坛系统便携运行包

使用方式
1. 解压交付包到任意英文或中文路径。
2. 双击 start.bat 或 start-portable.bat。
3. 等待窗口显示 “Services are ready.”。
4. 浏览器会自动打开 http://localhost:4173。

默认管理员账号
admin / admin123456

便携包说明
- 便携包内置 Java 运行时，目标机器不需要预装 Java。
- 便携包不需要 Node.js、Maven、MySQL 或 Redis。
- 后端使用 demo profile 和 H2 文件数据库，数据保存在 app/backend/data。
- 前端由 app/frontend-server.jar 提供静态资源服务，并自动代理 /api 到后端。
- 停止系统可关闭启动窗口，或双击 stop.bat / stop-portable.bat。
- 请只通过 start.bat 或 start-portable.bat 启动，不要直接运行 runtime 目录下的 java.exe。

常用地址
- 前端首页：http://localhost:4173
- 后端接口：http://localhost:8080/api
- H2 控制台：http://localhost:8080/api/h2-console

如果端口冲突
- 后端默认端口：8080
- 前端默认端口：4173
- 可在 PowerShell 中运行：
  .\start-portable.ps1 -BackendPort 8081 -FrontendPort 4174
