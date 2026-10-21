# 课设

所属课程：[网络空间安全技术](../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [data/](data/README.md)
- [docs/](docs/README.md)
- [outputs/](outputs/README.md)
- [static/](static/README.md)
- [templates/](templates/README.md)
- [课程设计模版2026年/](%E8%AF%BE%E7%A8%8B%E8%AE%BE%E8%AE%A1%E6%A8%A1%E7%89%882026%E5%B9%B4/README.md)
- [app.py](app.py)
- [audit.py](audit.py)
- [ChatGPT Image 2026年6月10日 08_59_35.png](ChatGPT%20Image%202026%E5%B9%B46%E6%9C%8810%E6%97%A5%2008_59_35.png)
- [config.py](config.py)
- [db.py](db.py)
- [requirements.txt](requirements.txt)
- [run_tests.py](run_tests.py)
- [secure_login_app.spec](secure_login_app.spec)
- [security.py](security.py)
- [seed_data.py](seed_data.py)
- [test_html.py](test_html.py)
- [topic_1.pdf](topic_1.pdf)
- [打包运行说明_无Java依赖.md](%E6%89%93%E5%8C%85%E8%BF%90%E8%A1%8C%E8%AF%B4%E6%98%8E_%E6%97%A0Java%E4%BE%9D%E8%B5%96.md)

[返回上级目录](../README.md)

## 原有项目说明

# Web 登录系统安全加固与审计日志设计

> 《网络空间安全技术》课程设计 · 题目 1
> 设计者：程泽凯　学号：2023112621
> **本项目仅在本地授权环境中开发与测试，未对任何真实第三方系统造成影响。**

一个带安全加固与审计能力的最小 Web 登录系统：密码加盐哈希存储、登录失败限制与账号锁定、
登录审计日志、四类异常登录检测、安全审计输出。

## 目录结构

```
课设/
├── config.py          # 全局配置 + 个性化安全阈值（答辩可现场改）
├── db.py              # SQLite 数据访问层（参数化查询）
├── security.py        # 口令哈希 / 强度校验 / 失败限制 / 登录认证
├── audit.py           # 实时异常检测 + 离线全量审计
├── app.py             # Flask 主应用与路由
├── seed_data.py       # 生成个性化测试账号与模拟异常日志
├── run_tests.py       # 自动化测试（8 用例 / 18 断言）
├── requirements.txt
├── templates/         # 页面模板
├── static/style.css   # 样式
├── data/              # SQLite 数据库（运行后自动生成）
└── docs/
    ├── 课程设计报告.md
    ├── 流程图.md        # 5 张 Mermaid 流程图
    └── 截图清单.md      # 报告所需截图指引
```

## 环境要求

- Python 3.10+（实测 3.13.5）
- 依赖：`pip install -r requirements.txt`

## 快速开始

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成个性化测试数据（4 个账号 + 模拟异常日志）
python seed_data.py

# 3. 运行自动化测试（应输出 18/18 通过）
python run_tests.py

# 4. 启动 Web 系统
python app.py
# 浏览器访问 http://127.0.0.1:5000/
```

## 主要页面

| 路由 | 说明 |
|------|------|
| `/register` | 用户注册（口令强度校验） |
| `/login` | 用户登录（可填“模拟来源 IP”演示异地登录） |
| `/dashboard` | 个人中心（账号状态 + 我的登录记录） |
| `/audit` | 安全审计（运行全量审计，展示告警与日志） |

## 演示要点（答辩可现场操作）

1. **触发锁定**：用错误口令连续登录 5 次，第 5 次后账号被锁定 10 分钟。
2. **异地登录**：登录时在“模拟来源 IP”填不同 IP（如 10.0.0.5 / 172.16.8.9），10 分钟内 ≥2 个 IP 即告警。
3. **现场改阈值**：编辑 `config.py`（如 `MAX_FAILED_ATTEMPTS = 3`），重跑 `python run_tests.py` 或刷新 `/audit` 验证变化。

## 个性化安全阈值（见 config.py）

| 规则 | 阈值 |
|------|------|
| 暴力尝试 | 5 分钟内失败 ≥ 5 次 → 锁定 10 分钟 |
| 异地登录 | 10 分钟内 ≥ 2 个不同 IP |
| 非工作时间 | 23:00–06:00 |
| 高频登录 | 60 秒内 ≥ 10 次 |

