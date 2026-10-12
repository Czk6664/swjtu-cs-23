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
