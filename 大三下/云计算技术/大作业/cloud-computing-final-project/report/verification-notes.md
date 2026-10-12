# Verification Notes

## Completed Locally

- File existence check passed with `scripts/check-files.ps1`.
- Python syntax compilation passed for all generated `.py` files.
- Backend Flask smoke test passed outside Docker after installing dependencies from the Tsinghua PyPI mirror into a temporary directory.
- `docker compose config` passed after adding configurable mirror-backed base image arguments.
- Kubernetes YAML files and `spark/sparkapplication.yaml` passed local YAML parsing with PyYAML.
- Secret scan passed with `scripts/scan-secrets.ps1`.

## Requires Real Local/Cloud Runtime

- Full `docker compose up --build -d` could not complete on this machine because Docker image pulling for `python:3.11-slim` from the configured mirror timed out. The frontend image built successfully, but the backend image still needs a successful Python base image pull.
- `kubectl apply --dry-run=client` could not be used without a reachable Kubernetes API server in the active Docker/CCE context. YAML syntax was validated locally instead.
- CCE node readiness, ELB access, PVC persistence, ConfigMap Volume update, HPA scaling, and Spark Operator execution must be verified on the actual Huawei Cloud environment.

## Recommended Retest Commands

```bash
docker pull docker.m.daocloud.io/library/python:3.11-slim
docker compose up --build -d
curl http://localhost:5000/api/ping
curl http://localhost:5000/api/visit
```

If the mirror is unavailable, replace `PYTHON_IMAGE` in `.env` with another reachable mirror or pre-pull `python:3.11-slim` through Docker Desktop's configured registry mirror.
