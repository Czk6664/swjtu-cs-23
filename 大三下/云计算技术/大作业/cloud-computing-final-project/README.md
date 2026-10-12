# 云计算技术结束大作业

身份信息：

- 姓名：程泽凯，王晨羽
- 学号：2023112621,2023114337
- 班级：2023-04班

本目录放在 D 盘课程作业工作区下，作为云计算技术结束大作业工程。它覆盖必做 100 分：第一部分 CCE/K8s 平台搭建 50 分，第二部分 Spark 大数据分析方向 40 分，报告质量 10 分。

## 目录结构

```text
cloud-computing-final-project/
  backend/                 # Flask API
  frontend/                # Nginx 静态页和反向代理
  k8s/                     # Huawei Cloud CCE YAML
  spark/                   # Spark 方向 A 大作业内容
  report/                  # 报告正文、截图清单、图表目录
  scripts/                 # 本地辅助脚本
  docker-compose.yml
  .env.example
```

## 镜像源建议

后端 Dockerfile 默认使用清华 PyPI 镜像：

```bash
docker compose build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

Docker 基础镜像默认走可配置镜像源：

```text
PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim
NGINX_IMAGE=docker.m.daocloud.io/library/nginx:1.25-alpine
REDIS_IMAGE=docker.m.daocloud.io/library/redis:7-alpine
```

Docker Desktop 可在设置中加入 registry mirrors，例如：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com"
  ]
}
```

镜像源可用性会变化，实际教学时以当前网络可访问源为准。

## 1. 本地运行

复制环境变量文件：

```powershell
Copy-Item .env.example .env
```

启动本地三容器：

```bash
docker compose up --build
```

验收：

```bash
curl http://localhost:5000/api/ping
curl http://localhost:5000/api/visit
```

浏览器打开：

```text
http://localhost:8080
```

截图要点：

- 首页显示程泽凯，王晨羽、2023112621,2023114337、2023-04班。
- `/api/ping` 返回 `{"status":"ok"}`。
- 后端日志显示收到请求。

## 2. 推送镜像到 SWR

```bash
docker login -u cn-north-4@<AK> -p <SK> swr.cn-north-4.myhuaweicloud.com
docker tag cloud-course-backend:v1 swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/backend:v1
docker tag cloud-course-frontend:v1 swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/frontend:v1
docker push swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/backend:v1
docker push swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/frontend:v1
```

截图要点：SWR 控制台镜像列表包含镜像名称和 Tag。

## 3. CCE 部署

进入 `k8s/`：

```bash
kubectl apply -f secret.yaml
kubectl apply -f configmap.yaml
kubectl apply -f redis-pvc.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-configmap.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f services.yaml
```

验证：

```bash
kubectl get nodes -o wide
kubectl get pods
kubectl get svc backend-svc
curl http://<ELB_IP>/api/ping
```

## 4. Redis PVC 验证

```bash
kubectl get pvc
kubectl exec -it <redis-pod-name> -- redis-cli -a <your_password> SET testkey "hello"
kubectl exec -it <redis-pod-name> -- redis-cli -a <your_password> GET testkey
kubectl delete pod <redis-pod-name>
kubectl exec -it <new-redis-pod-name> -- redis-cli -a <your_password> GET testkey
```

## 5. ConfigMap Volume 验证

修改 `k8s/frontend-configmap.yaml` 中 `server backend-svc:5000;` 为 `server backend-svc:5001;`，然后：

```bash
kubectl apply -f k8s/frontend-configmap.yaml
kubectl rollout restart deployment/frontend
kubectl exec -it <frontend-pod-name> -- cat /etc/nginx/conf.d/default.conf
```

报告说明：

- ConfigMap Volume 适合 Nginx 配置、证书、配置文件这类文件型配置，Pod 内可以按文件路径读取。
- `envFrom` 适合 Redis 地址、端口、运行环境等小型键值配置，应用通过环境变量读取。

## 6. HPA 验证

```bash
kubectl top nodes
kubectl apply -f k8s/hpa.yaml
kubectl get hpa
kubectl get pods -w
```

压测：

```bash
ab -n 10000 -c 200 http://<ELB_IP>/api/ping
```

没有 `ab` 时可用：

```bash
python scripts/hpa-load-test.py --url http://<ELB_IP>/api/ping --requests 10000 --concurrency 200
```

## 7. Spark 方向 A

进入 `spark/` 阅读 [spark/README.md](spark/README.md)。核心流程：

```bash
helm install spark-op ./spark-operator-chart/ -n spark-operator --create-namespace
kubectl apply -f spark/sparkapplication.yaml
kubectl get pods -n default
kubectl logs <driver-pod-name>
```

## 8. 报告材料

- 报告正文：[report/report.md](report/report.md)
- 截图清单：[report/screenshot-checklist.md](report/screenshot-checklist.md)
- 附录文档：[report/appendix-template.md](report/appendix-template.md)
- 本机验证记录：[report/verification-notes.md](report/verification-notes.md)

## 9. 安全说明

不要提交以下内容：

- 华为云 AK/SK。
- kubeconfig。
- Redis 真实密码。
- OBS 访问密钥。
- SWR 登录 token。

本大作业仅保留占位符，真实值应通过 `.env`、控制台或本地命令临时注入。
