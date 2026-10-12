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

