# 截图清单

| 编号 | 截图内容 | 命令或位置 | 对应分项 |
| --- | --- | --- | --- |
| 1 | 本地前端首页显示程泽凯，王晨羽、2023112621,2023114337、2023-04班 | `http://localhost:8080` | 任务1 |
| 2 | 本地后端返回 ping | `curl http://localhost:5000/api/ping` | 任务1 |
| 3 | 后端日志显示收到请求 | `docker compose logs backend` | 任务1 |
| 4 | SWR 控制台镜像列表含 backend/frontend 和 Tag | 华为云 SWR 控制台 | 任务1 |
| 5 | CCE 节点 Ready 且 VERSION >= 1.27 | `kubectl get nodes -o wide` | 任务2 |
| 6 | Pod 均为 Running | `kubectl get pods` | 任务3 |
| 7 | 后端 ELB 公网 IP 可访问 `/api/ping` | `curl http://<ELB_IP>/api/ping` | 任务3 |
| 8 | PVC 为 Bound | `kubectl get pvc` | 任务4 |
| 9 | Redis 写入 `testkey` | `redis-cli SET testkey "hello"` | 任务4 |
| 10 | 删除 Redis Pod 后重建 | `kubectl delete pod <redis-pod-name>` | 任务4 |
| 11 | 重建后 `GET testkey` 返回 `hello` | `redis-cli GET testkey` | 任务4 |
| 12 | ConfigMap Volume 文件内容更新 | `cat /etc/nginx/conf.d/default.conf` | 任务5 |
| 13 | HPA 初始状态 | `kubectl get hpa` | 任务6 |
| 14 | 压测时 Pod 扩容 | `kubectl get pods -w` | 任务6 |
| 15 | 停止压测后 Pod 缩容 | `kubectl get pods -w` | 任务6 |
| 16 | Spark Driver 和 Executor Pod | `kubectl get pods -n default` | A-0 |
| 17 | Spark Driver 日志含 Schema 和前 5 行 | `kubectl logs <driver-pod-name>` | A-1 |
| 18 | Spark 缺失值统计和清洗前后行数 | `kubectl logs <driver-pod-name>` | A-1 |
| 19 | Spark 四类查询结果 | `kubectl logs <driver-pod-name>` | A-2 |
| 20 | 性能对比表和图 | `report/charts/` | A-3 |

截图要求：文字清晰，包含 Pod 名称、状态、返回值、时间或 Tag 等关键信息。
