# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository scope

This is a **university course directory** (智能交通 / Intelligent Transportation) containing several
distinct deliverables side by side. The active software project lives at the repo **root**
(`apps/`, `services/`, `openspec/`); the `大作业*` / `课程设计` / `期末作业` folders are
self-contained homework artifacts (papers, experiment data, LaTeX, PPTs) that the root app reads
from but does not build.

When asked to work on "the app" / "the demo" / "the system", you almost always mean the root project,
**not** the homework folders. Treat each `大作业N` folder as a separate sub-repo (大作业2 even has its
own `CLAUDE.md` covering its YOLO experiments + LaTeX report).

| Path | What it is |
|------|------------|
| `apps/web` | React 19 + Vite + TypeScript frontend (single large `App.tsx`) |
| `services/api` | FastAPI backend, model orchestration, task execution |
| `openspec/changes/*` | Spec-driven proposals/designs/tasks (the source of truth for intent) |
| `大作业1` | Traffic-flow forecasting experiment (STAEformer). Root backend reads its `results/*.json` |
| `大作业2` | Traffic-sign detection experiment (YOLO/TT100K). Root backend reads its run dir + dataset yaml |
| `课程设计` | Early static HTML/CSS/JS prototype (reference only) |

## Root project: 智能交通管理决策系统 (Traffic Decision System)

A demo that fuses two course experiments (forecasting + detection) into a single "analyze scene →
decision" workflow, then optionally spawns async report/voice/summary generation tasks.

### Commands

One-shot launch (opens two PowerShell windows: backend :8000, frontend :5173):
```powershell
.\start-demo.ps1
```

Backend alone:
```powershell
cd services/api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
uvicorn app.main:app --reload      # http://127.0.0.1:8000  (docs at /docs)
```

Frontend alone:
```powershell
cd apps/web
npm install
npm run dev        # http://127.0.0.1:5173
npm run build      # tsc -b && vite build
```

Backend tests (pytest is not in `pyproject.toml` deps — install it first):
```powershell
cd services/api
.venv\Scripts\Activate.ps1
pip install pytest
pytest                                   # all tests
pytest tests/test_wsl_hermes.py          # single file
pytest tests/test_wsl_hermes.py::test_name   # single test
```

Config: copy `.env.example` to `.env` at the repo **root** (not in `services/api`). `config.py`
resolves `ROOT_DIR` as 3 parents up and loads `ROOT_DIR/.env`. Absolute Windows paths in `.env`
point at the homework result dirs.

## Architecture (big picture)

### Request flow
`POST /api/analyze-scene` → `workflow.build_analysis_payload` → `OrchestrationService.analyze`.
The orchestrator fans out to three injected services and merges their dicts:

- **`ForecastService`** — reads JSON files from `大作业1/results/` (`baseline_*`, `dgl_*`), returns metric summary. Skipped when `workflow == detection-only`.
- **`DetectionService`** — reads the TT100K dataset yaml (`names`) + last row of `results.csv` from the 大作业2 run dir. Skipped when `workflow == prediction-only`.
- **`DecisionService`** — currently a **rule-based stub** that assembles facts/risk/recommendation strings. The stated roadmap is to replace this with a real LLM call (OpenAI config already wired in settings).

The merged result is persisted via `InMemoryResultStore` and returned with a `result_id`
(fetch later via `GET /api/results/{id}`).

### Async tasks
Report/voice generation are decoupled from the analyze request. `analyze-scene` (with
`include_report` / `include_voice`) or `POST /api/tasks` enqueue into `InMemoryTaskManager`, which
spawns an `asyncio.create_task` running `HermesAdapter.run_task`. Poll state via
`GET /api/tasks` / `GET /api/tasks/{id}` — frontend uses polling, there are no websockets.

**Important:** all stores (`InMemoryResultStore`, `InMemoryTaskManager`) are in-process and reset on
restart. `TASK_BACKEND` / `REDIS_URL` settings exist but the Redis backend is not yet implemented.

### Hermes / WSL bridge — the main subtlety
Task execution generates Markdown reports / voice scripts via the **Hermes agent**, which does not
run natively on Windows. The design (see README + `openspec/changes/windows-project-wsl-hermes-integration`):

- Frontend + FastAPI stay on Windows; Hermes runs inside WSL2.
- `HermesAdapter.run_task` shells out via `wsl.exe -d <distro> --cd <wsl-path> hermes chat ...`.
- `wsl_bridge.py` (`WslPathMapper`) maps Windows paths (`D:\...`) → WSL mounts (`/mnt/d/...`).
- On FastAPI **startup**, `validate_runtime_dependencies` runs preflight checks (distro exists, workspace reachable, `command -v hermes`) and **fails fast** if `HERMES_ENABLED=true` but the environment is broken.
- When `HERMES_ENABLED=false` (the default), `HermesAdapter` returns **stub artifacts** instead — this is the normal local-dev path. Don't assume WSL/Hermes is available.

Per-task artifacts and logs are written under `services/api/.task_state/` (gitignored): payloads,
prompts, and outputs (`reports/`, `audio/`, `summaries/`).

### Frontend
`apps/web/src/App.tsx` is a single ~900-line component holding the entire UI. It talks to the
backend directly via `API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"`
(absolute URL — **there is no Vite dev proxy**). Detection preview images come from
`GET /api/assets/detection/{name}` (allow-listed filenames only). Other charts are static files in
`apps/web/public/experiment-charts/`.

## Conventions specific to this codebase

- Dependencies are wired manually in `app/dependencies.py` (module-level singletons), not via a DI framework. Add a new service there and inject it into `OrchestrationService`.
- Service `summarize()` methods are defensive: missing result files return `{}` / empty rather than raising, so the demo still runs without the homework data present.
- Enums (`WorkflowType`, `TaskType`, `TaskState`) in `models.py` use kebab-case string values (`"full-decision"`, `"daily-summary"`) — match these exactly in requests.
- `openspec/changes/` is the design record. Before non-trivial changes to the root app, check the relevant change folder (`proposal.md` / `design.md` / `tasks.md`) for intended behavior.
