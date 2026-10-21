## 1. Project Scaffold

- [x] 1.1 Create `cloud-computing-final-project/` under the current D drive workspace.
- [x] 1.2 Create subdirectories for `backend`, `frontend/static`, `k8s`, `spark`, `report/screenshots`, `report/charts`, and `scripts`.
- [x] 1.3 Add a root `.gitignore` that excludes secrets, kubeconfig files, local caches, generated logs, and temporary report exports.
- [x] 1.4 Add a `.env.example` with placeholder values for Redis password, SWR Region, SWR organization, image names, and OBS input path.

## 2. Local Backend Implementation

- [x] 2.1 Implement `backend/app.py` with Flask routes for `/api/ping`, Redis-backed visit recording, and useful request logging.
- [x] 2.2 Add `backend/requirements.txt` with Flask, Redis client, and at least one extra Python package required by the task book.
- [x] 2.3 Add `backend/Dockerfile` using a multi-stage build and a configurable `PIP_INDEX_URL` defaulting to a China-friendly mirror source.
- [x] 2.4 Add backend environment variable handling for `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, and `APP_ENV`.
- [x] 2.5 Verify the backend can run locally outside Docker with environment variables when Python dependencies are installed.

## 3. Local Frontend and Compose Implementation

- [x] 3.1 Implement `frontend/static/index.html` with a clean verification page showing 程泽凯，王晨羽, 2023112621,2023114337, and 2023-04班.
- [x] 3.2 Add `frontend/nginx.conf` that proxies `/api/` requests to the backend service and serves static content.
- [x] 3.3 Add `frontend/Dockerfile` using `nginx:1.25-alpine` and copying static files plus Nginx config.
- [x] 3.4 Add `docker-compose.yml` with backend, frontend, and Redis services connected by service names.
- [x] 3.5 Add compose ports for local verification: frontend on 8080, backend on 5000, and Redis on 6379.
- [ ] 3.6 Verify `docker compose up --build` starts all services and `/api/ping` returns `{"status":"ok"}`.

## 4. Huawei Cloud Kubernetes Manifests

- [x] 4.1 Add `k8s/backend-deployment.yaml` with two replicas, SWR image placeholder, resource requests/limits, ConfigMap env, Secret env, and liveness probe.
- [x] 4.2 Add `k8s/redis-deployment.yaml` with one Redis replica, memory limit no greater than 512Mi, and PVC mount at `/data`.
- [x] 4.3 Add `k8s/services.yaml` with backend LoadBalancer Service using Huawei Cloud ELB annotation and Redis ClusterIP Service.
- [x] 4.4 Add `k8s/configmap.yaml` for backend non-secret Redis configuration.
- [x] 4.5 Add `k8s/secret.yaml` as a safe template with `<REDIS_PASSWORD_BASE64>` placeholder and encoding instructions.
- [x] 4.6 Add `k8s/redis-pvc.yaml` using `storageClassName: csi-disk` and a 10Gi request.
- [x] 4.7 Add `k8s/frontend-configmap.yaml` containing full Nginx `default.conf` for ConfigMap Volume mounting.
- [x] 4.8 Add `k8s/frontend-deployment.yaml` that mounts the ConfigMap to `/etc/nginx/conf.d/default.conf`.
- [x] 4.9 Add `k8s/hpa.yaml` with minReplicas 1, maxReplicas 4, and CPU target utilization 60%.
- [x] 4.10 Add `k8s/README.md` with the correct `kubectl apply` order and verification commands.

## 5. Spark Final Project Workload

- [x] 5.1 Add `spark/sparkapplication.yaml` using Spark Operator fields and replaceable teacher-provided SWR PySpark image.
- [x] 5.2 Add `spark/wordcount.py` as the introductory Spark job aligned with the task book.
- [x] 5.3 Add `spark/analysis.py` that reads OBS or local sample data, prints schema and first five rows, calculates missing ratios, and applies two missing-value strategies.
- [x] 5.4 Implement at least four named Spark SQL/DataFrame analyses covering GROUP BY, Top-N ordering, time trend analysis, and JOIN or window function.
- [x] 5.5 Add `spark/performance_compare.py` or equivalent helper for recording Pandas, PySpark 1 executor, and PySpark 2 executor timings.
- [x] 5.6 Add sample data or a sample schema description so the Spark scripts are understandable before the real OBS dataset path is supplied.
- [x] 5.7 Add Spark run instructions covering Helm Spark Operator install, job submission, log capture, and screenshot points.

## 6. Final Project Report Pack

- [x] 6.1 Add `cloud-computing-final-project/README.md` with end-to-end runbook commands for local Docker, SWR push, CCE deploy, Redis PVC test, ConfigMap Volume test, HPA test, and Spark test.
- [x] 6.2 Add `report/report.md` with cover information for 程泽凯，王晨羽, 2023112621,2023114337, 2023-04班 and all required report sections.
- [x] 6.3 Add `report/screenshot-checklist.md` mapping each required screenshot to the scoring item and command that produces it.
- [x] 6.4 Add `report/appendix-template.md` for Dockerfile, YAML, and Python code references.
- [x] 6.5 Add a short explanation section comparing ConfigMap Volume mounts and `envFrom`.
- [x] 6.6 Add HPA analysis text covering metrics collection delay, HPA evaluation interval, cooldown behavior, and cost savings.
- [x] 6.7 Add Amdahl analysis template for Spark performance results and non-linear speedup causes.

## 7. Verification

- [x] 7.1 Run a file existence check for all expected cloud-computing-final-project files.
- [x] 7.2 Run YAML syntax validation where local tooling is available.
- [x] 7.3 Run Docker Compose config validation with `docker compose config` if Docker is available.
- [ ] 7.4 Run a local build/start smoke test if Docker is available.
- [x] 7.5 Document any verification commands that cannot run locally because they require Huawei Cloud resources.
- [x] 7.6 Confirm no real secrets or credentials are present in generated files.
