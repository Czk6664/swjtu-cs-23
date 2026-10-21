# Web 登录系统安全加固与审计日志设计 - 打包运行说明

## 说明

本项目为 Python Flask + SQLite 实现，不依赖 Java，也不需要安装 JDK/JRE。

已提供两种运行方式：

1. `exe` 打包版：适合答辩演示，双击即可启动本地 Web 服务。
2. Python 源码版：适合提交源代码和复现实验。

## exe 打包版运行

进入 `secure_login_app` 文件夹，双击：

```text
secure_login_app.exe
```

程序启动后浏览器访问：

```text
http://127.0.0.1:5000/
```

如果 5000 端口被占用，可在 PowerShell 中指定端口启动：

```powershell
$env:APP_PORT="5055"
.\secure_login_app.exe
```

然后访问：

```text
http://127.0.0.1:5055/
```

## 测试账号

```text
czk2023 / Czk@2023112621
alice99 / Alice#pass01
bob_dev / BobDev2024!
victim7 / Victim#0001
```

## 源码版运行

```powershell
pip install -r requirements.txt
python seed_data.py
python run_tests.py
python app.py
```

浏览器访问：

```text
http://127.0.0.1:5000/
```

## 目录说明

```text
app.py              Flask 主程序
security.py         注册、登录、哈希、锁定
audit.py            异常检测与安全审计
db.py               SQLite 数据访问
config.py           安全阈值配置
seed_data.py        生成测试账号和模拟日志
run_tests.py        自动化测试，使用独立测试数据库
templates/          页面模板
static/             页面样式
data/               SQLite 数据库
```

## 合规声明

本系统仅用于本地课程设计实验与答辩演示，所有账号、日志和异常记录均为本地模拟数据，未对任何真实第三方系统、公网服务器或校园网设备进行扫描、攻击或测试。
