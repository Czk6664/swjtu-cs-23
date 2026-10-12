# Huawei Cloud CCE 部署说明

本目录是课程设计第一部分的 CCE 部署清单。正式部署前必须替换：

- `swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/backend:v1`
- `swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/frontend:v1`
- `secret.yaml` 中的 `<REDIS_PASSWORD_BASE64>`

## 1. 推送镜像到 SWR

```bash
docker login -u cn-north-4@<AK> -p <SK> swr.cn-north-4.myhuaweicloud.com
docker tag cloud-course-backend:v1 swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/backend:v1
docker tag cloud-course-frontend:v1 swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/frontend:v1
docker push swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/backend:v1
docker push swr.cn-north-4.myhuaweicloud.com/<YOUR_ORG>/frontend:v1
```

## 2. 创建 Secret 密码

Linux/macOS/Git Bash:

```bash
echo -n "your_password" | base64
```

PowerShell:

```powershell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("your_password"))
```

把结果填入 `secret.yaml` 的 `data.password`。

## 3. 应用资源

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

## 4. 任务 2 验证 CCE 节点

```bash
kubectl get nodes -o wide
```

截图要求：至少 2 个 Worker 节点 `Ready`，并包含 `VERSION` 列，版本不低于 1.27。

## 5. 任务 3 验证应用部署

```bash
kubectl get pods
kubectl get svc backend-svc
curl http://<ELB_IP>/api/ping
```

期望返回：

```json
{"status":"ok"}
```

## 6. 任务 4 验证 Redis 持久化

```bash
kubectl get pvc
kubectl get pods -l app=redis
kubectl exec -it <redis-pod-name> -- redis-cli -a <your_password> SET testkey "hello"
kubectl exec -it <redis-pod-name> -- redis-cli -a <your_password> GET testkey
kubectl delete pod <redis-pod-name>
kubectl get pods -w
kubectl exec -it <new-redis-pod-name> -- redis-cli -a <your_password> GET testkey
```

截图要求：PVC 为 `Bound`，删除 Pod 前后 `GET testkey` 均返回 `hello`。

## 7. 任务 5 验证 ConfigMap Volume

修改 `frontend-configmap.yaml` 中的 `server backend-svc:5000;`，例如改成 `server backend-svc:5001;`，再执行：

```bash
kubectl apply -f frontend-configmap.yaml
kubectl rollout restart deployment/frontend
kubectl get pods -l app=frontend
kubectl exec -it <frontend-pod-name> -- cat /etc/nginx/conf.d/default.conf
```

截图要求：Pod 内文件内容已经变成 ConfigMap 中的新内容。

## 8. 任务 6 验证 HPA

```bash
kubectl top nodes
kubectl apply -f hpa.yaml
kubectl get hpa
kubectl get pods -w
```

另开终端压测：

```bash
ab -n 10000 -c 200 http://<ELB_IP>/api/ping
```

若无 `ab`，可用报告中的 Python/curl 并发脚本替代。截图要求：Pod 数量从 1 增加到 2 个或更多，停止压测后约 5 分钟缩回。
