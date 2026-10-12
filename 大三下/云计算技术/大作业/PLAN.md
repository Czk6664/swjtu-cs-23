# 云计算技术课程设计执行计划

来源：`课程设计任务书.docx`  
当前日期：2026-05-18  
提交截止：2026-06-15 22:00  

## 目标拆分

总分由三部分构成：

| 模块 | 分值 | 必做内容 |
| --- | ---: | --- |
| 第一部分：云计算平台搭建 | 50 | CCE 上部署 Flask API + Redis，两层 Web 应用，完成容器化、对外暴露、配置分离、持久化、HPA |
| 第二部分：并行编程实战 | 40 | Spark 大数据分析或 MPI 并行科学计算二选一 |
| 报告质量 | 10 | PDF 报告、截图、图表、代码仓库链接、附录 |
| 附加题 | +15 | 监控系统、CI/CD、前沿专题，三题各 +5 分，可选 |

建议默认选择方向 A：Spark 大数据分析。若你更擅长数值算法和 MPI 通信，也可以改选方向 B。

## 本机需要完成的内容

### 1. 准备本机工具和项目目录

- 安装或确认可用：Docker Desktop、Git、kubectl、Helm、Python 3、Node 或其他前端静态文件编辑工具。
- 安装压测工具：优先 `ab`，没有则用 Python `locust` 或自写 `curl` 并发脚本替代。
- 建立代码仓库，建议目录如下：

```text
cloud-course-project/
  backend/
    app.py
    requirements.txt
    Dockerfile
  frontend/
    static/index.html
    nginx.conf
    Dockerfile
  k8s/
    backend-deployment.yaml
    redis-deployment.yaml
    services.yaml
    configmap.yaml
    secret.yaml
    redis-pvc.yaml
    frontend-configmap.yaml
    frontend-deployment.yaml
    hpa.yaml
  spark/
    analysis.py
    performance_compare.py
  report/
    screenshots/
    charts/
    report.md
```

### 2. 第一部分本机开发

- 修改后端 Dockerfile：保留多阶段构建，在 `requirements.txt` 中加入至少 1 个自选 Python 包，例如 `requests` 或 `pandas`。
- 编写或整理 Flask 后端 API，至少保证 `/api/ping` 返回 `{"status":"ok"}`，并能访问 Redis。
- 修改前端 Nginx 静态页，在 `static/index.html` 中加入本人学号和姓名，方便验收识别。
- 编写 `docker-compose.yml`，本地启动 Flask + Redis，验证前后端通信正常。
- 本地构建镜像：

```bash
docker build -t backend:v1 ./backend
docker build -t frontend:v1 ./frontend
docker compose up
```

- 截图保存：本地页面、后端日志收到请求、容器运行状态。
- 准备推送到 SWR 的命令，替换 `<REGION>`、`<ORG>`、`<AK>`、`<SK>`：

```bash
docker login -u <REGION>@<AK> -p <SK> swr.<REGION>.myhuaweicloud.com
docker tag backend:v1 swr.<REGION>.myhuaweicloud.com/<ORG>/backend:v1
docker tag frontend:v1 swr.<REGION>.myhuaweicloud.com/<ORG>/frontend:v1
docker push swr.<REGION>.myhuaweicloud.com/<ORG>/backend:v1
docker push swr.<REGION>.myhuaweicloud.com/<ORG>/frontend:v1
```

### 3. 第一部分 YAML 文件编写

- 后端 Deployment：副本数 2，镜像来自 SWR，配置 `resources.requests` 和 `resources.limits`，通过 ConfigMap 注入 Redis 地址，通过 Secret 注入 Redis 密码。
- Redis Deployment：副本数 1，内存限制不超过 512Mi。
- Service：后端使用 `LoadBalancer` 并添加华为云 ELB 注解，Redis 使用 `ClusterIP`。
- ConfigMap：保存 `REDIS_HOST=redis-svc`、`REDIS_PORT=6379` 等非敏感配置。
- Secret：Redis 密码必须 base64 编码，不在 YAML 中明文出现。
- PVC：使用 `storageClassName: csi-disk`，Redis 挂载 `/data`。
- 前端 ConfigMap Volume：将 `nginx.conf` 以 Volume 挂载到 `/etc/nginx/conf.d/default.conf`。
- HPA：后端 `minReplicas=1`、`maxReplicas=4`、CPU 目标利用率 60%。

### 4. 第二部分本机开发

默认路线：方向 A Spark。

- 编写 `spark/analysis.py`，完成数据读取、Schema 打印、前 5 行展示、缺失值统计、两种缺失值处理策略。
- 完成至少 4 个 Spark SQL 或 DataFrame 查询：
  - GROUP BY 聚合。
  - ORDER BY Top-N。
  - 按年或按月的时间趋势分析。
  - JOIN 操作或窗口函数。
- 编写 `spark/performance_compare.py`，对同一个查询做 Pandas 单机、PySpark 1 executor、PySpark 2 executor 的耗时对比。
- 在本机生成性能对比图，报告中结合 Amdahl 定律分析加速比不线性的原因。

替代路线：方向 B MPI。

- 实现一个串行算法和 MPI 并行算法，建议选数值积分或矩阵乘法。
- 为每个 MPI 通信原语添加注释，说明数据流向。
- 准备 1、2、4 进程性能测试脚本，生成运行时间表和加速比折线图。
- 将关键通信改为 `Isend` / `Irecv`，对比阻塞版和非阻塞版。

### 5. 报告和提交材料

- 在本机整理 PDF 报告，建议章节：
  - 封面：课程名、学号、姓名、班级、日期。
  - 华为云环境信息：Region、CCE 集群版本、节点规格。
  - 第一部分任务 1-6：步骤摘要、关键截图、问题与解决方案。
  - 第二部分所选方向：代码说明、运行截图、性能图表、Amdahl 分析。
  - 总结与收获：不少于 200 字。
  - 附录：Dockerfile、YAML、核心 Python 代码或仓库链接。
- 建立 GitHub 或 Gitee 仓库，上传代码和 YAML。
- 最终提交：PDF 报告 + 代码仓库链接，邮件主题格式为 `【云计算课设】学号_姓名`。

## 华为云需要完成的内容

### 1. 账号与资源准备

- 注册并实名认证华为云账号。
- 通过“智能基座”入口申请代金券，课程代码：`SCAI004712`。
- 选定 Region，建议全程保持同一个 Region，例如 `cn-north-4`，避免 SWR、CCE、OBS 跨区域不可用。
- 开通或准备以下服务：
  - SWR：存放后端和前端镜像。
  - CCE：托管 Kubernetes 集群。
  - ELB：由 LoadBalancer Service 自动创建公网访问入口。
  - OBS：方向 A Spark 数据集读取使用。
  - EVS 云硬盘：Redis PVC 持久化使用。

### 2. SWR 镜像仓库

- 在 SWR 控制台创建组织 `<ORG>`。
- 本机推送 `backend:v1` 和 `frontend:v1` 到 SWR。
- 在 SWR 控制台截图，必须包含镜像名称和 Tag。

### 3. CCE 集群搭建

- 在 CCE 控制台创建 Kubernetes 集群：
  - Kubernetes 版本：不低于 1.27。
  - 网络插件：Yangtse CNI 默认配置即可。
  - Worker 节点：2 个，建议 2 vCPU / 4 GB；资源不足时再加 2 vCPU / 8 GB。
  - Master 节点由华为云托管，不需要自己管理。
- 下载 KubeConfig，配置本机 `kubectl` 或使用 CloudShell。
- 截图验收：

```bash
kubectl get nodes -o wide
```

要求所有 Worker 节点 `STATUS` 为 `Ready`，截图中包含 `VERSION` 列。

### 4. 应用部署与验证

- 在 CCE 上按顺序应用 YAML：

```bash
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis-pvc.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/services.yaml
```

- 验证 Pod：

```bash
kubectl get pods
```

要求所有 Pod 为 `Running`。

- 验证公网访问：

```bash
curl http://<ELB_IP>/api/ping
```

要求返回 `{"status":"ok"}`，截图浏览器或 curl 结果。

### 5. Redis 持久化验证

- 查看 PVC：

```bash
kubectl get pvc
```

要求 `redis-data-pvc` 为 `Bound`。

- 写入测试数据：

```bash
kubectl exec -it <redis-pod-name> -- redis-cli SET testkey "hello"
kubectl exec -it <redis-pod-name> -- redis-cli GET testkey
```

- 删除 Redis Pod 触发重建：

```bash
kubectl delete pod <redis-pod-name>
kubectl get pods -w
```

- 重建后再次查询 `GET testkey`，要求仍返回 `"hello"`。
- 截图要求：`kubectl get pvc`、写入数据、删除 Pod、重建后查询结果。

### 6. ConfigMap Volume 挂载验证

- 部署前端 ConfigMap 和前端 Deployment。
- 修改 ConfigMap 中后端端口，例如 `5000` 改为 `5001`，执行 `kubectl apply`。
- 进入前端 Pod 验证挂载文件更新：

```bash
kubectl exec -it <frontend-pod-name> -- cat /etc/nginx/conf.d/default.conf
```

- 截图保存文件内容。
- 报告中说明：
  - Volume 挂载适合配置文件、Nginx 配置、证书等文件型配置。
  - `envFrom` 适合环境变量形式的小型键值配置，例如 Redis 地址、端口、运行环境。

### 7. HPA 弹性伸缩验证

- 确认 metrics-server 可用：

```bash
kubectl top nodes
```

- 创建 HPA：

```bash
kubectl apply -f k8s/hpa.yaml
kubectl get hpa
```

- 一个窗口监控 Pod：

```bash
kubectl get pods -w
```

- 另一个窗口压测：

```bash
ab -n 10000 -c 200 http://<ELB_IP>/api/ping
```

- 截图要求：
  - Pod 从 1 个扩容到 2 个或更多。
  - 停止压测后约 5 分钟缩回 1 个。
  - `kubectl get hpa` 或 `kubectl describe hpa` 的状态。
- 报告分析：
  - 扩容延迟来自 metrics 采集周期和 HPA 评估间隔。
  - 冷却时间用于避免频繁扩缩容。
  - HPA 可在低负载时减少副本数，从而节省资源成本。

### 8. 第二部分华为云执行

默认路线：方向 A Spark。

- 在 CCE 上安装 Spark Operator：

```bash
helm install spark-op ./spark-operator-chart/ -n spark-operator --create-namespace
```

- 将教师提供的数据集 OBS 路径填入 Spark 程序或配置。
- 修改 `sparkapplication.yaml`：
  - `image` 替换为教师提供的 SWR PySpark 镜像地址。
  - `executorInstances=2`。
  - `executorMemory="1g"`。
- 先提交 `wordcount.py` 示例，验证 Driver Pod 变为 `Completed`。
- 再提交自己的 `analysis.py`，完成清洗、查询和统计。
- 截图要求：
  - `kubectl get pods -n default`，包含 Driver 和 Executor Pod。
  - Driver 日志中的 Schema、前 5 行、缺失值比例、SQL 查询结果。
  - 1 executor 和 2 executor 的性能对比结果。

替代路线：方向 B MPI。

- 在 CCE 上部署 MPI Operator：

```bash
kubectl apply -f mpi-operator.yaml
```

- 修改 `mpijob.yaml`：
  - `image` 替换为教师提供的 SWR mpi4py 镜像。
  - `slotsPerWorker=2`。
  - `workerReplicas=2`。
- 运行 `pi_mpi.py` 示例，截图 Launcher Pod 日志，必须包含估算的 π 值。
- 运行自己的串行版、MPI 阻塞版、MPI 非阻塞版程序，截图结果一致性和性能数据。

### 9. 附加题可选路线

- 监控系统：在 CCE 部署 kube-prometheus-stack，Grafana 展示节点 CPU 折线图和 Pod 内存柱状图。
- CI/CD：用 GitHub Actions 或 GitLab CI 完成提交代码后自动构建镜像、推送 SWR、更新 K8s Deployment。
- 前沿专题：选择分布式 AI 训练或 K3s + MQTT，形成不少于 1500 字专题内容。

建议优先做 CI/CD，和第一部分镜像构建、SWR、K8s 部署衔接最自然。

### 10. 实验结束释放资源

- 删除不再使用的 LoadBalancer Service，避免 ELB 继续计费。
- 删除 CCE Worker 节点或整个 CCE 集群。
- 删除未使用的 EVS 云硬盘、OBS 临时数据、SWR 旧镜像 Tag。
- 保留报告所需截图后再释放资源。

## 截图证据清单

| 编号 | 截图内容 | 对应分项 |
| --- | --- | --- |
| 1 | 本地 `docker compose up`，后端日志显示收到请求 | 任务1 |
| 2 | 前端首页包含学号姓名 | 任务1 |
| 3 | SWR 镜像列表，包含 backend/frontend 镜像和 Tag | 任务1 |
| 4 | `kubectl get nodes -o wide`，Worker Ready，VERSION >= 1.27 | 任务2 |
| 5 | `kubectl get pods`，应用 Pod Running | 任务3 |
| 6 | 浏览器或 curl 访问 `<ELB_IP>/api/ping` 返回 `{"status":"ok"}` | 任务3 |
| 7 | `kubectl get pvc`，PVC Bound | 任务4 |
| 8 | Redis 写入 testkey | 任务4 |
| 9 | 删除 Redis Pod 并重建 | 任务4 |
| 10 | 重建后 `GET testkey` 仍返回 hello | 任务4 |
| 11 | exec 进入前端 Pod 查看挂载的 `default.conf` | 任务5 |
| 12 | HPA 扩容时 Pod 数增加 | 任务6 |
| 13 | HPA 缩容时 Pod 数回落 | 任务6 |
| 14 | Spark Driver + Executor Pod 或 MPI Launcher + Worker Pod | 第二部分 |
| 15 | 数据清洗、查询结果、性能图表 | 第二部分 |

## 时间安排

| 日期 | 目标 |
| --- | --- |
| 2026-05-18 至 2026-05-22 | 完成本机代码框架、Dockerfile、docker compose、本地联调 |
| 2026-05-23 至 2026-05-29 | 开通华为云资源、推送 SWR、创建 CCE、完成任务 1-3 |
| 2026-05-30 至 2026-06-03 | 完成 Redis PVC、ConfigMap Volume、HPA，补齐第一部分截图 |
| 2026-06-04 至 2026-06-09 | 完成第二部分 Spark 或 MPI 方向，生成性能数据和图表 |
| 2026-06-10 至 2026-06-13 | 写报告、整理附录、检查截图清晰度和代码仓库 |
| 2026-06-14 | 预提交自查，确认 PDF、仓库链接、邮件主题 |
| 2026-06-15 22:00 前 | 正式提交 |

## 当前下一步

1. 确认个人信息：学号、姓名、班级、组队成员和分工比例。
2. 确认第二部分选择 Spark 还是 MPI。
3. 在本机建立代码仓库和目录结构。
4. 先完成任务 1 的本地 `docker compose` 联调，这是后续 SWR、CCE、HPA 的基础。
