# MySQL 本地与服务器部署方案

本项目现在推荐本地和服务器统一使用 MySQL。`demo` profile 仍保留为无数据库依赖的 H2 备用模式，但正常开发、验收和部署建议使用 `mysql` profile。

## 1. 数据库方案

- 数据库：MySQL 8.x
- 数据库名：`swjtu_forum`
- 字符集：`utf8mb4`
- 排序规则：`utf8mb4_unicode_ci`
- 后端 profile：`mysql`
- 建表方式：Spring Data JPA `ddl-auto=update` 自动同步实体结构
- 初始化数据：启动时自动创建管理员、板块、标签、圈子和演示帖子

## 2. 本地 MySQL 初始化

先确认本地 MySQL 服务已启动，然后在项目根目录执行：

```powershell
mysql -u root -p < init-database.sql
```

如果你的 MySQL 不是 root 用户，也可以手动执行：

```sql
CREATE DATABASE IF NOT EXISTS swjtu_forum
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

## 3. 本地启动

默认启动脚本已经切到 MySQL：

```powershell
$env:DB_USERNAME = "root"
$env:DB_PASSWORD = "你的MySQL密码"
$env:JWT_SECRET = "swjtu-forum-local-jwt-secret-change-me"
.\start.ps1
```

如果本机 MySQL 端口、用户名或库名不同，可以显式指定：

```powershell
$env:DB_URL = "jdbc:mysql://localhost:3306/swjtu_forum?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true"
$env:DB_USERNAME = "root"
$env:DB_PASSWORD = "你的MySQL密码"
$env:JWT_SECRET = "swjtu-forum-local-jwt-secret-change-me"
.\start.ps1
```

启动后访问：

- 前端：`http://localhost:4173`
- 后端：`http://localhost:8080/api`
- 默认管理员：`admin / admin123456`

## 4. 服务器 MySQL 初始化

建议在服务器上创建独立数据库用户，不要直接使用 root：

```bash
sudo mysql
```

```sql
CREATE DATABASE IF NOT EXISTS swjtu_forum
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'swjtu_forum'@'localhost'
  IDENTIFIED BY '请替换成强密码';

GRANT ALL PRIVILEGES ON swjtu_forum.* TO 'swjtu_forum'@'localhost';
FLUSH PRIVILEGES;
```

## 5. 服务器后端启动命令

你的服务器已有 `80` 和 `8000` 被占用，论坛后端建议使用 `8081`，并且只让 Nginx 反向代理访问：

```bash
export DB_URL='jdbc:mysql://127.0.0.1:3306/swjtu_forum?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true'
export DB_USERNAME='swjtu_forum'
export DB_PASSWORD='请替换成强密码'
export JWT_SECRET='请替换成至少32位的随机密钥'

java -Dfile.encoding=UTF-8 \
  -Dspring.profiles.active=mysql \
  -jar forum-1.0.0.jar \
  --server.port=8081
```

## 6. Nginx 推荐代理

推荐使用子域名，例如 `forum.example.com`。这样不会影响服务器上已有的网站：

```nginx
server {
    listen 80;
    server_name forum.example.com;

    root /opt/swjtu-forum/frontend/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8081/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

检查配置并重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 7. 是否保留演示数据

`mysql` profile 默认会写入演示数据，便于课程设计验收。如果正式公开运行前不想自动补充演示数据，可以设置：

```bash
export DEMO_SEED_ENABLED=false
```

基础管理员和基础板块仍会由 `app.bootstrap.enabled=true` 初始化。

## 8. 备用 H2 启动

如果临时没有 MySQL，只想快速打开项目：

```powershell
.\start.ps1 -SpringProfile demo
```

这个模式只适合临时演示，不建议作为服务器部署方案。
