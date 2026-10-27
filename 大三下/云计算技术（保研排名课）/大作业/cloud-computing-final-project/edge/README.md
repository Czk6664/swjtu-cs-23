# edge

<!-- directory-guide:start -->
## 本层内容介绍

这里是“云计算技术”课程下的“edge”目录，主要用于整理该主题的配套文件或下级模块。

**阅读建议：**先看下方内容摘要选择入口；需要了解整体任务时返回上级项目或课程说明。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **7 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

| 子目录 | 内容与用途 |
| --- | --- |
| [gateway](gateway/README.md) | 包含依赖或构建配置的项目目录 |
| [k8s](k8s/README.md) | 部署配置或集群资源定义 |
| [simulator](simulator/README.md) | 包含依赖或构建配置的项目目录 |

本层没有直接存放正文资料，请从上表进入相应目录。

<!-- directory-guide:end -->

所属课程：[云计算技术](../../../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [gateway/](gateway/README.md)
- [k8s/](k8s/README.md)
- [simulator/](simulator/README.md)

[返回上级目录](../README.md)

## 原有项目说明

# C-2 Edge Computing Simulation: K3s + MQTT

This directory contains a small edge-to-cloud pipeline used for the course extra task.

- `simulator/edge_sensor.py`: local edge sensor simulator. In the report it is described as the workload running on an edge node/K3s side.
- `gateway/mqtt_to_redis.py`: cloud-side MQTT consumer that writes telemetry into Redis.
- `k8s/mqtt-broker.yaml`: Mosquitto MQTT Broker running in Kubernetes.
- `k8s/mqtt-redis-gateway.yaml`: MQTT-to-Redis gateway Deployment running in CCE.

Data flow:

```text
Edge simulator -> MQTT Broker in CCE -> MQTT-to-Redis Gateway -> Redis
```

Verification commands:

```powershell
kubectl apply -f edge/k8s/mqtt-broker.yaml
kubectl apply -f edge/k8s/mqtt-redis-gateway.yaml
kubectl port-forward svc/mqtt-broker 1883:1883
python edge/simulator/edge_sensor.py --host 127.0.0.1 --count 10
kubectl logs deploy/mqtt-redis-gateway
kubectl exec deploy/redis -- redis-cli -a redis2026 XRANGE edge:sensor:stream - + COUNT 5
```

