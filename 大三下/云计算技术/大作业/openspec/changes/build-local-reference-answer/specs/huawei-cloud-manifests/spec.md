## ADDED Requirements

### Requirement: SWR image placeholders
The Kubernetes manifests SHALL reference Huawei Cloud SWR image placeholders that can be replaced with the teacher's actual Region and organization.

#### Scenario: Image placeholder is visible
- **WHEN** a teacher opens the backend or frontend Deployment YAML
- **THEN** the image field clearly indicates the SWR image value that must be replaced before deployment

### Requirement: Backend and Redis workloads
The manifests SHALL define backend and Redis workloads matching the task book requirements.

#### Scenario: Backend deployment is rubric-aligned
- **WHEN** the backend Deployment YAML is reviewed
- **THEN** it declares two backend replicas, container port 5000, resource requests and limits, ConfigMap-based non-secret config, and Secret-based Redis password injection

#### Scenario: Redis deployment is rubric-aligned
- **WHEN** the Redis Deployment YAML is reviewed
- **THEN** it declares one Redis replica and a memory limit no greater than 512Mi

### Requirement: Services for external and internal access
The manifests SHALL expose the backend through a LoadBalancer Service and Redis through a ClusterIP Service.

#### Scenario: Backend service is externally reachable
- **WHEN** the service YAML is applied to CCE
- **THEN** the backend Service requests a Huawei Cloud ELB-compatible LoadBalancer with the required annotation

#### Scenario: Redis service remains internal
- **WHEN** the service YAML is applied to CCE
- **THEN** Redis is exposed only through a ClusterIP Service named for backend internal access

### Requirement: Redis persistent storage
The manifests SHALL include a Redis PVC using Huawei Cloud `csi-disk` storage and mount it at `/data`.

#### Scenario: Redis data survives pod recreation
- **WHEN** Redis writes `testkey` and the Redis Pod is deleted and recreated
- **THEN** the recreated Redis Pod can still return the stored value from the PVC

### Requirement: ConfigMap Volume Nginx configuration
The manifests SHALL include a ConfigMap Volume mount for Nginx reverse-proxy configuration.

#### Scenario: Mounted config can be inspected
- **WHEN** the frontend Pod is running
- **THEN** `cat /etc/nginx/conf.d/default.conf` inside the Pod shows the ConfigMap-provided Nginx configuration

### Requirement: HPA scaling manifest
The manifests SHALL include a backend HPA with minReplicas 1, maxReplicas 4, and CPU utilization target 60%.

#### Scenario: HPA manifest applies
- **WHEN** `kubectl apply -f k8s/hpa.yaml` is run against CCE
- **THEN** `kubectl get hpa` shows an HPA targeting the backend Deployment
