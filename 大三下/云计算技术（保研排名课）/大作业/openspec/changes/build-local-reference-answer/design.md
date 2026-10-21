## Context

The workspace is on the D drive at `D:\大三下\云计算技术\大作业`. The Word task book requires a full 100-point final project: local containerized application work, Huawei Cloud CCE deployment assets, Spark or MPI parallel programming evidence, and a polished report. The requested final project will use the identity 程泽凯，王晨羽 / 2023112621,2023114337 / 2023-04班 and will be suitable for teacher demonstration, with cloud-specific values kept as placeholders.

The existing workspace currently contains the course task book and a high-level `PLAN.md`; there is no runnable source tree yet. The implementation should create a new `cloud-computing-final-project/` directory under the current D drive workspace rather than scattering files at the repository root.

## Goals / Non-Goals

**Goals:**

- Produce a local, runnable reference application with Flask backend, Redis, Nginx frontend, Dockerfiles, and Docker Compose.
- Prefer mirror-source friendly configuration for Python packages and package manager operations where practical.
- Provide CCE-ready Kubernetes manifests matching the grading rubric for tasks 1-6.
- Provide a Spark direction-A reference workload to cover the 40-point parallel programming section.
- Provide report scaffolding, command runbooks, and evidence checklists for a teacher-quality final project.
- Keep all real cloud secrets out of versioned files.

**Non-Goals:**

- Provision real Huawei Cloud resources automatically.
- Commit AK/SK, kubeconfig, Redis real password, OBS bucket credentials, or SWR login tokens.
- Generate final screenshots, because they must come from the user's actual local Docker run and Huawei Cloud environment.
- Complete optional +15 bonus work unless requested separately after the 100-point baseline is implemented.

## Decisions

1. **Use `cloud-computing-final-project/` as the implementation root.**

   Rationale: the workspace already contains planning and source Word files. A separate implementation root makes the teacher final project easy to zip, publish, or hand out without mixing OpenSpec artifacts and generated notes.

   Alternative considered: placing files directly in the workspace root. This was rejected because it makes the directory noisy and harder to distribute.

2. **Use Flask + Redis + Nginx with Docker Compose for the local reference stack.**

   Rationale: this directly matches the Word task book and gives students visible local evidence: frontend page with identity, backend `/api/ping`, backend Redis access, and backend logs.

   Alternative considered: adding a heavier frontend framework. This was rejected because the rubric asks for an Nginx static page, not a SPA.

3. **Use mirror-friendly dependency configuration without hard-coding private mirrors everywhere.**

   Rationale: Dockerfiles can use pip mirror arguments such as `PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`, while still allowing users to override the value. This improves build reliability in China without making the answer brittle.

   Alternative considered: using only public defaults. This was rejected because the user explicitly asked to prefer mirror sources.

4. **Use placeholders for cloud image and credential values.**

   Rationale: the final project is for teaching and should be safe to publish. Values such as `<REGION>`, `<ORG>`, `<SWR_BACKEND_IMAGE>`, `<OBS_INPUT_PATH>`, and `<REDIS_PASSWORD_BASE64>` document what must change without leaking secrets.

   Alternative considered: embedding concrete Huawei Cloud credentials. This is unsafe and not appropriate for a final project.

5. **Choose Spark direction A as the baseline 40-point parallel programming path.**

   Rationale: Spark aligns well with OBS datasets, SQL analysis, and report charts. It is also easier to package as a repeatable final project with sample/local fallback data than an MPI cluster job that depends on MPI Operator details.

   Alternative considered: MPI direction B. MPI remains a valid future extension, but implementing both directions is not required for the 100-point baseline.

6. **Include scripts and documentation that generate report-ready artifacts, not final fake evidence.**

   Rationale: a teacher final project should show how to run and verify the system. Screenshots must reflect the actual execution environment, while commands and expected outputs can be provided as run guidance.

   Alternative considered: creating simulated screenshots. This was rejected because it could confuse students and weaken the final project's credibility.

## Risks / Trade-offs

- **[Risk] Docker base image pulls may still be slow or blocked.** → Mitigation: document Docker daemon registry mirror configuration and keep image choices small (`python:3.11-slim`, `nginx:1.25-alpine`, `redis:7-alpine`).
- **[Risk] Huawei Cloud CCE annotations and StorageClass names can vary by Region or cluster version.** → Mitigation: keep YAML aligned with the task book and add comments for values that must be confirmed in the console.
- **[Risk] Spark jobs cannot fully run locally without a real Spark runtime or teacher-provided image.** → Mitigation: include code that is valid for Spark on CCE and include a small sample-data path plus clear CCE submission instructions.
- **[Risk] HPA may not trigger during short tests if metrics-server or resource requests are misconfigured.** → Mitigation: provide `kubectl top`, `kubectl describe hpa`, and pressure-test fallback guidance.
- **[Risk] Report materials may drift from code behavior.** → Mitigation: include a command checklist and screenshots checklist tied to concrete files and commands.

## Migration Plan

1. Create `cloud-computing-final-project/` with source, Docker, Kubernetes, Spark, and report directories.
2. Implement and validate local Docker Compose flow.
3. Fill CCE manifests with placeholders and verification comments.
4. Implement Spark scripts and sample analysis outputs/charts.
5. Add report scaffold and README runbook.
6. Run local formatting and static checks where available.

Rollback is simple: remove the generated `cloud-computing-final-project/` directory and keep the OpenSpec change artifacts for later re-implementation.

## Open Questions

- Which Huawei Cloud Region and SWR organization will be used in the final demonstration?
- What OBS dataset path will the teacher provide for Spark analysis?
- Should optional bonus reference material (+15) be added after the mandatory 100-point baseline?
