# 云计算技术课程设计实验报告

## 封面

- 课程名称：云计算技术
- 姓名：程泽凯，王晨羽
- 学号：2023112621,2023114337
- 班级：2023-04班
- 日期：2026年春季学期
- 分工说明：个人完成或按实际组队情况填写

## 一、华为云环境信息

- Region：`cn-north-4` 或实际 Region
- CCE 集群版本：填写 `kubectl get nodes -o wide` 中 VERSION
- Worker 节点规格：建议 2 vCPU / 4 GB，2 个 Worker
- 使用服务：SWR、CCE、ELB、OBS、EVS

截图：`kubectl get nodes -o wide`

## 二、第一部分：云计算平台搭建

### 任务1：应用容器化

本任务完成 Flask 后端、Nginx 前端和 Redis 的本地容器化联调。后端 Dockerfile 保留多阶段构建结构，并在 `requirements.txt` 中加入 `requests` 作为自选 Python 包。前端首页展示姓名、学号和班级，用于验收识别。

关键命令：

```bash
docker compose up --build
curl http://localhost:5000/api/ping
curl http://localhost:5000/api/visit
```

截图：

- 本地前端页面。
- 后端日志收到请求。
- SWR 镜像列表，包含 backend/frontend 镜像和 Tag。

### 任务2：CCE 集群搭建

通过华为云 CCE 创建 Kubernetes 集群，Worker 节点 2 个，Kubernetes 版本不低于 1.27，网络插件使用 Yangtse CNI 默认配置。

截图：

```bash
kubectl get nodes -o wide
```

### 任务3：应用部署

在 CCE 中部署后端、Redis、前端、ConfigMap、Secret 和 Service。后端 Service 使用 LoadBalancer 类型，由华为云 ELB 提供公网 IP；Redis Service 使用 ClusterIP，仅集群内部访问。

关键命令：

```bash
kubectl get pods
kubectl get svc backend-svc
curl http://<ELB_IP>/api/ping
```

期望返回：

```json
{"status":"ok"}
```

### 任务4：持久化存储

Redis 使用 `redis-data-pvc` 挂载到 `/data`，StorageClass 为 `csi-disk`。通过写入 `testkey`、删除 Redis Pod、重建后再次查询证明数据未丢失。

关键命令：

```bash
kubectl get pvc
kubectl exec -it <redis-pod-name> -- redis-cli -a <password> SET testkey "hello"
kubectl delete pod <redis-pod-name>
kubectl exec -it <new-redis-pod-name> -- redis-cli -a <password> GET testkey
```

### 任务5：ConfigMap Volume 挂载

Nginx 的反向代理配置通过 ConfigMap Volume 挂载到 `/etc/nginx/conf.d/default.conf`。修改 ConfigMap 后重启前端 Deployment，进入 Pod 查看文件内容，验证配置文件已更新。

Volume 挂载适合 Nginx 配置、证书、应用配置文件等文件型配置；`envFrom` 更适合 Redis 地址、端口、运行环境等少量键值型配置。Volume 方式让程序像读取普通文件一样读取配置，`envFrom` 则在进程启动时注入环境变量。

### 任务6：HPA 弹性伸缩

后端 HPA 配置为 `minReplicas=1`、`maxReplicas=4`、CPU 目标利用率 60%。压测时观察 Pod 数量增加，停止压测后等待缩容。

扩容延迟主要来自 metrics-server 的采集周期和 HPA 控制器的评估间隔，因此 CPU 升高后不会立刻扩容。缩容冷却时间可以防止负载短时间波动导致频繁扩缩容。HPA 在低负载时减少副本，在高负载时增加副本，兼顾可用性和云资源成本。

## 三、第二部分：Spark 大数据分析

### A-0 环境部署

安装 Spark Operator 并提交 `SparkApplication`。截图 Driver 和 Executor Pod，Driver 完成后查看日志。

### A-1 数据清洗

`analysis.py` 读取数据后输出 Schema、前 5 行、缺失值比例。对 `rating` 采用 `dropna`，因为评分是后续排序和聚合的核心指标；对 `genre`、`country`、`vote_count` 采用 `fillna`，因为这些字段缺失时仍可保留样本用于总体统计。

### A-2 Spark SQL 统计分析

本大作业包含以下分析：

- 按类型 GROUP BY，统计电影数量和平均评分。
- 按评分与投票数 ORDER BY，输出 Top-N 影片。
- 按年份分析电影数量和平均评分趋势。
- 使用窗口函数统计每个类型内部评分前三。
- 使用 JOIN 方式将类型映射到更粗粒度分组后聚合。

每个查询结果截图后，补充不少于 50 字的业务分析说明。

### A-3 性能对比与 Amdahl 分析

记录 Pandas、PySpark 1 executor、PySpark 2 executor 三种方式的执行时间。实测加速比通常低于理论线性加速，原因包括 Spark 任务启动开销、数据序列化、Shuffle、网络通信、调度开销以及程序中不可并行部分。

Amdahl 定律公式：

```text
S(p) = 1 / ((1 - f) + f / p)
```

其中 `f` 为可并行比例，`p` 为并行进程或 executor 数。可根据 2 executor 的实测加速比反推 `f`，再解释理论值与实测值差异。

## 四、总结与收获

本次课程设计将容器镜像、Kubernetes 编排、云负载均衡、持久化存储、配置分离和弹性伸缩串联成完整实践。通过本地 Docker Compose 可以先验证应用逻辑，再将镜像推送到 SWR 并部署到 CCE，体现了从开发到云端运行的基本流程。Spark 部分进一步展示了云平台上运行并行数据分析任务的方式，也说明并行计算的加速效果会受到通信、调度和不可并行部分影响。整体来看，云计算技术不是单一工具，而是一套围绕应用交付、资源调度、弹性和可观测性的工程体系。

## 五、附录

附录可粘贴或引用以下文件：

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `docker-compose.yml`
- `k8s/*.yaml`
- `spark/analysis.py`
- `spark/performance_compare.py`
