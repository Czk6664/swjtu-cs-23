## Why

The course project requires a complete, reproducible final project that teachers can use to demonstrate the local development, container build, Huawei Cloud deployment, and report evidence flow. Creating the scaffold now gives the implementation a clear target: full-score coverage for the Word task book while keeping cloud-specific secrets and resources replaceable.

## What Changes

- Create a local final project implementation for the Flask backend, Nginx frontend, Redis integration, Dockerfiles, and Docker Compose workflow.
- Provide Docker and Python dependency configuration that prefers China-friendly mirror sources where practical, and stores project artifacts under the D drive workspace.
- Add Kubernetes YAML reference manifests for Huawei Cloud CCE, including Deployments, Services, ConfigMap, Secret template, PVC, ConfigMap Volume mount, and HPA.
- Add a Spark direction-A reference workload and supporting scripts for data cleaning, SQL analysis, and performance comparison materials.
- Add report/cloud-computing-final-project materials using the teacher-provided identity: 程泽凯，王晨羽, 2023112621,2023114337, 2023-04班.
- Keep implementation safe for publication by using placeholders for Huawei Cloud SWR organization, image registry, AK/SK, OBS bucket paths, and Redis password.

## Capabilities

### New Capabilities

- `local-web-stack`: Covers the local Flask API, Redis integration, Nginx frontend, Dockerfiles, Docker Compose setup, and mirror-source friendly build configuration.
- `huawei-cloud-manifests`: Covers CCE-ready Kubernetes resources for application deployment, persistent Redis storage, ConfigMap Volume mounting, and HPA scaling verification.
- `spark-reference-workload`: Covers Spark direction-A reference code for data cleaning, SQL analytics, and Pandas vs PySpark performance comparison.
- `reference-report-pack`: Covers teacher-facing reference documentation, evidence checklist, and report scaffold using the provided student identity.

### Modified Capabilities

- None.

## Impact

- Adds a new cloud-computing-final-project project tree under the D drive course workspace.
- Adds Dockerfiles, Docker Compose configuration, backend/frontend source files, Kubernetes YAML manifests, Spark scripts, report scaffolding, and README/runbook documentation.
- Requires local Docker, kubectl, Helm, Python, and optional ApacheBench or an equivalent pressure-test script.
- Uses Huawei Cloud SWR/CCE/ELB/EVS/OBS concepts through configurable placeholders; no real credentials are committed.
