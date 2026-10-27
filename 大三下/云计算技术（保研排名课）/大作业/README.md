# 大作业

<!-- directory-guide:start -->
## 本层内容介绍

这里是“云计算技术”课程下的“大作业”目录，主要用于整理该项课程实践的相关材料，具体内容见下方文件与子目录。

**阅读建议：**先读任务或报告了解目标，再看代码、数据和结果；借鉴方法后独立完成自己的任务。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **469 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

| 子目录 | 内容与用途 |
| --- | --- |
| [cloud-computing-final-project](cloud-computing-final-project/README.md) | 该主题的配套文件或下级模块 |
| [cloud-report-tex](cloud-report-tex/README.md) | 文档排版源文件及配套资源 |
| [openspec](openspec/README.md) | 项目中该主题的需求、设计或任务记录 |
| [tools](tools/README.md) | 处理数据、生成材料或辅助运行的脚本工具 |
| [课程设计模版_视觉计算2026年](%E8%AF%BE%E7%A8%8B%E8%AE%BE%E8%AE%A1%E6%A8%A1%E7%89%88_%E8%A7%86%E8%A7%89%E8%AE%A1%E7%AE%972026%E5%B9%B4/README.md) | 课程文档或报告的模板及配套文件 |

- **配置及其他配套文件（1 份）**：[.gitignore](.gitignore)。
- **文档与说明（2 份）**：[PLAN.md](PLAN.md)、[课程设计任务书.docx](%E8%AF%BE%E7%A8%8B%E8%AE%BE%E8%AE%A1%E4%BB%BB%E5%8A%A1%E4%B9%A6.docx)。
- **表格与数据（1 份）**：[douban_movies.csv](douban_movies.csv)。

<!-- directory-guide:end -->

所属课程：[云计算技术](../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [cloud-computing-final-project/](cloud-computing-final-project/README.md)
- [cloud-report-tex/](cloud-report-tex/README.md)
- [openspec/](openspec/README.md)
- [tools/](tools/README.md)
- [课程设计模版_视觉计算2026年/](%E8%AF%BE%E7%A8%8B%E8%AE%BE%E8%AE%A1%E6%A8%A1%E7%89%88_%E8%A7%86%E8%A7%89%E8%AE%A1%E7%AE%972026%E5%B9%B4/README.md)
- [.gitignore](.gitignore)
- [douban_movies.csv](douban_movies.csv)
- [PLAN.md](PLAN.md)
- [课程设计任务书.docx](%E8%AF%BE%E7%A8%8B%E8%AE%BE%E8%AE%A1%E4%BB%BB%E5%8A%A1%E4%B9%A6.docx)

[返回上级目录](../README.md)

## 原有项目说明

# 西南交通大学云计算技术大作业

本仓库用于提交“云计算技术”课程大作业，包含 CCE/Kubernetes 应用部署、Redis 持久化、ConfigMap 配置管理、HPA 弹性伸缩、Spark 大数据分析、边缘计算与监控扩展，以及最终实验报告材料。

## 项目信息

- 课程：云计算技术
- 学校：西南交通大学
- 学生：程泽凯、王晨羽
- 学号：2023112621、2023114337
- 班级：2023-04 班

## 仓库内容

```text
.
├── cloud-computing-final-project/   # 云计算大作业核心工程
│   ├── backend/                     # Flask 后端 API
│   ├── frontend/                    # Nginx 静态前端与反向代理
│   ├── k8s/                         # Kubernetes/CCE 部署清单
│   ├── spark/                       # Spark 大数据分析方向代码
│   ├── edge/                        # 边缘计算扩展实验
│   ├── monitoring/                  # Prometheus/Grafana 监控配置
│   ├── scripts/                     # 本地验证与辅助脚本
│   └── docker-compose.yml           # 本地 Docker Compose 编排
├── cloud-report-tex/                # 实验报告 LaTeX 源码、图表与 PDF
├── PLAN.md                          # 实验规划与任务拆解
├── 课程设计任务书.docx              # 课程设计任务书
└── douban_movies.csv                # Spark 分析使用的豆瓣电影数据集备份
```

## 功能概述

本项目主要完成以下内容：

- 使用 Docker Compose 在本地运行前端、后端和 Redis。
- 使用 Kubernetes YAML 在华为云 CCE 上部署前后端服务、Redis、PVC、ConfigMap、Secret 和 Service。
- 验证 Redis PVC 持久化能力，证明 Pod 重建后数据仍可保留。
- 使用 ConfigMap Volume 管理 Nginx 配置，并对比环境变量注入方式。
- 配置 HPA，通过压测观察副本数自动扩缩容。
- 使用 Spark Operator 运行 PySpark 作业，对豆瓣电影数据集进行清洗、类型聚合、Top-N 查询、窗口排名和性能对比。
- 扩展实现边缘数据采集、CI/CD 构建部署和监控看板。
- 形成完整实验报告与截图材料。

## 快速运行

进入核心工程目录：

```bash
cd cloud-computing-final-project
```

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

本地启动服务：

```bash
docker compose up --build
```

验证后端接口：

```bash
curl http://localhost:5000/api/ping
curl http://localhost:5000/api/visit
```

浏览器访问：

```text
http://localhost:8080
```

## Kubernetes 部署

在 `cloud-computing-final-project` 目录下执行：

```bash
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis-pvc.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-configmap.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/services.yaml
```

检查资源：

```bash
kubectl get pods
kubectl get svc
kubectl get pvc
```

HPA 验证：

```bash
kubectl apply -f k8s/hpa.yaml
kubectl get hpa
kubectl get pods -w
```

更详细的部署步骤见 [cloud-computing-final-project/README.md](cloud-computing-final-project/README.md)。

## Spark 大数据分析

Spark 方向代码位于：

```text
cloud-computing-final-project/spark/
```

核心文件：

- `analysis.py`：PySpark 数据清洗、查询与性能计时代码。
- `pandas_douban_performance.py`：Pandas 单机性能对比。
- `sparkapplication-douban-perf-1.yaml`：1 executor 性能实验。
- `sparkapplication-douban-perf-2.yaml`：2 executors 性能实验。
- `generate_douban_report_figures.py`：生成报告图表。

性能对比覆盖 CSV 读取、跨行解析、评分清洗、类型拆分和聚合排序全过程，用于报告中的 Amdahl 分析。

## 实验报告

报告材料位于：

```text
cloud-report-tex/
```

主要文件：

- `main_report.tex`：报告 LaTeX 源码。
- `main_report_final.pdf`：最终报告 PDF。
- `云计算大作业实验报告.pdf`：中文命名版报告。
- `figures/`：实验截图、性能图和监控图。

## 大文件说明

课程提供的离线资源包、容器镜像 tar 包和本地工具目录体积较大，未纳入 Git 仓库。相关内容已通过 `.gitignore` 排除，包括：

- `云计算课程设计_离线资源包_SparkOperator+MPI+Monitoring.zip`
- `云计算课程设计_离线资源包_SparkOperator+MPI+Monitoring/`
- `*.tar`
- `tools/`

这些文件仅用于本地环境搭建，不影响仓库中代码和报告的阅读。

## 安全说明

仓库不应包含真实云账号凭据。请勿提交以下内容：

- 华为云 AK/SK
- kubeconfig
- SWR 登录 token
- OBS 访问密钥
- 生产环境 Redis 密码

当前仓库中的 `.env.example`、Secret YAML 等仅用于课程实验示例，真实值应在本地或云控制台中配置。


