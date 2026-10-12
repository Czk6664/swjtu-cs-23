# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository scope

This directory (`期末作业`) is the **capstone / final project** of the 智能交通 course. It is now
**implemented and runnable offline** under `src/capstone/` (see "Project structure" / "Common
commands"). The two core contributions — **decision fusion** (`orchestration/`) and the **data
flywheel** (`flywheel/`) — are built and verified; per the standing "模型先不下载" constraint the
flywheel's retrain step is a deterministic *simulation* (demonstrating the closed loop, gating, and
rollback), swappable for real training without interface changes.

The goal is to integrate the three prior assignments into one system:

> **大小模型协同的智能交通管理决策系统**
> A big-small model collaborative intelligent traffic management & decision system, driven by a
> **data flywheel (数据飞轮)** that periodically retrains and optimizes the small models.

This is an **integrative** assignment, not a from-scratch one. The expectation is to *reuse* and *orchestrate*
the work in `大作业1` / `大作业2` / `大作业3`, add a big model (LLM) decision/orchestration layer on top,
and close the loop with continuous model improvement.

## Parent-repo context (what you are reusing)

This folder lives inside `D:\大三下\智能交通`, a multi-assignment course workspace. The capstone draws on:

| Source | Role in the capstone | Model size class |
|--------|----------------------|------------------|
| `大作业1` | **Traffic-flow forecasting** — STAEformer (PyTorch). Datasets: METRLA, PEMSBAY, PEMS03/04/07/08. Produces `results/*.json` metric summaries. | small (specialist) |
| `大作业2` | **Traffic-sign / object detection** — YOLO (Ultralytics) on a 12-class TT100K subset. Produces run dirs with `results.csv`, confusion matrices, prediction grids. | small (specialist) |
| `大作业3` | **Conversational travel Q&A** — DeepSeek 1–7B + local RAG (scraped Chengdu traffic bulletins) on the Dify framework. Implements intent routing → retrieval/tools → grounded answer; also wraps 大作业1/2 as forecasting/detection Q&A tools. | LLM layer host (NL interface + RAG) |
| `services/api` (root) | Existing **FastAPI orchestration + WSL-Hermes task layer** and the in-memory result/task stores. The capstone extends this rather than replacing it. | — |
| `apps/web` (root) | Existing React 19 + Vite operator UI. | — |

Before building anything new, follow the workspace convention (see `~/.claude` rules): **search for an
existing implementation first** — most pieces already exist in the sibling folders and the root app.

## Core concept: 大小模型协同 (big-small model collaboration)

The architecture splits work by **cost and capability**:

- **Small models = specialists, always-on, cheap, structured.** STAEformer forecasting (大作业1) and
  YOLO detection (大作业2). They run frequently, produce structured numeric outputs, and are the
  things the data flywheel retrains.
- **Big model = generalist reasoner, on-demand, expensive, natural-language.** An LLM that
  **fuses** the small-model outputs into a situational judgment, explains *why*, drafts operator
  reports / voice broadcasts, and decides *which* small model to invoke for a given query. **大作业3
  already implements this layer's skeleton** (router → RAG retrieval / tool calls → LLM answer, with a
  pluggable DeepSeek provider) plus a local RAG knowledge base — the capstone extends it with the
  decision/fusion logic and the flywheel rather than starting from the root `DecisionService` stub.

This maps directly onto the existing root backend: the small-model outputs are already surfaced by
`ForecastService` and `DetectionService` (`services/api/app/services/`), and the `DecisionService`
is currently a **rule-based stub** explicitly marked for LLM replacement — that LLM is the "big model"
of the capstone. OpenAI settings are already wired in `services/api/app/config.py`
(`OPENAI_BASE_URL` / `OPENAI_API_KEY` / `OPENAI_MODEL`).

Division of labor the big model should follow:
1. **Route** — pick which small model(s) / knowledge base to call from the user/scene request
   (reuse 大作业3's intent router).
2. **Fuse** — combine forecast + detection + RAG-retrieved knowledge into one risk assessment / answer.
3. **Explain & act** — produce a decision with rationale, recommended action, and risk level.
4. **Generate** — reports / voice scripts / daily summaries (the existing Hermes task pipeline).
5. **Curate (flywheel)** — flag low-confidence / disagreeing / anomalous cases for re-labeling.

## The data flywheel (数据飞轮) — the new contribution

This is the part that does **not** exist yet and is the heart of the capstone. The loop:

```
 deploy small models ─▶ run inference on live/replayed traffic data
        ▲                              │
        │                              ▼
 retrain & evaluate            collect predictions + telemetry
        ▲                              │
        │                              ▼
 curate dataset  ◀──  mine hard cases (low confidence, model
 (auto + human/LLM label)       disagreement, big-model corrections,
                                 anomalies, low-rated Q&A / retrieval misses)
```

Concrete responsibilities to design/implement:

- **Collection** — persist every small-model inference with inputs, outputs, confidence, and
  timestamp. **Storage is Parquet + files (locked):** telemetry → date/model-partitioned Parquet;
  registry + dataset-snapshot metadata → JSON/YAML. The root app's in-memory stores are not used here.
- **Hard-case mining** — selection rules: low detection confidence, forecast error above threshold
  once ground truth arrives, **big-model vs small-model disagreement**, out-of-distribution / novel
  signs, operator corrections, and **RAG retrieval misses / low-rated answers** (feed back into the
  knowledge base or fine-tuning set). This is where the big model earns its keep as a labeler.
- **Curation / labeling** — auto-label with the big model + optional human-in-the-loop review;
  version every dataset snapshot so retraining is reproducible.
- **Retraining trigger** — scheduled (e.g. nightly/weekly) **and/or** threshold-based (drift /
  accumulated-hard-cases). The existing WSL-Hermes async task pattern in
  `services/api/app/services/hermes.py` + `task_manager.py` is a natural place to host long-running
  retrain jobs; reuse it rather than inventing a new scheduler.
- **Gated promotion** — never auto-deploy. Retrain → evaluate on a held-out benchmark → compare
  against the current production checkpoint → promote only if metrics improve and no regression on a
  safety subset → keep the previous checkpoint for rollback. Track a model registry (version,
  dataset snapshot, metrics, status: staging/production/archived).
- **Monitoring** — track per-model accuracy over time and **data/concept drift** so the flywheel can
  prove it is improving, not degrading.

Design principle: **the flywheel must be observable and reversible.** Every retrain must be traceable
to a dataset snapshot and comparable to the prior model, with a one-command rollback.

## Project structure (implemented)

```text
期末作业/
├── src/capstone/
│   ├── config.py         # 阈值/路径配置；解析到 workspace 内大作业目录；挂载大作业3 travelqa
│   ├── models/           # 小模型适配器 → 统一 Signal(risk, confidence, summary, raw)
│   │   ├── base.py       # Signal 数据类
│   │   ├── forecast.py   # 大作业1 STAEformer（复用 travelqa.ForecastTool）
│   │   ├── detection.py  # 大作业2 YOLO/TT100K（复用 travelqa.DetectionTool）
│   │   └── dialog_rag.py # 大作业3 TravelQAApp：RAG 知识信号 + LLM 解释出口
│   ├── orchestration/    # ★ 决策融合
│   │   ├── router.py     # 选择调用哪些小模型/知识库（workflow 或场景推断）
│   │   ├── fusion.py     # 加权置信融合 → SituationAssessment(risk_score/level/contributions)
│   │   └── decision.py   # 决策+可解释理由+协同分歧检测（替换根 DecisionService 桩）
│   ├── flywheel/         # ★ 数据飞轮（核心贡献）
│   │   ├── collector.py  # 遥测落 Parquet(按 模型/日期 分区；pyarrow 缺失回退 JSONL)
│   │   ├── miner.py      # 难例挖掘（低置信/分歧/标记）
│   │   ├── labeler.py    # 自动标注 + 版本化数据集快照(manifest)
│   │   ├── trainer.py    # 重训候选（当前确定性模拟，接口可换真实训练）
│   │   ├── evaluator.py  # 门控：主指标提升达标且安全子集不回归才放行
│   │   └── registry.py   # 模型版本注册表 + promote/rollback
│   └── pipeline.py       # TrafficDecisionSystem: decision_flow() / flywheel_round()
├── configs/thresholds.yaml
├── scripts/              # run_pipeline.py · simulate_flywheel.py · trigger_retrain.py
├── data/                 # telemetry(Parquet) / snapshots / registry  ← 运行后生成, gitignore
├── design.md  README.md
```

The **decision/orchestration logic** is decoupled from each small model behind thin adapters in
`models/` (uniform `Signal`), so a retrained checkpoint is swapped via the registry/config, not code.

## Decisions locked for this capstone

These were confirmed with the user and are no longer open questions:

- **Integration path = standalone `期末作业/` package.** Build the capstone here as its own package;
  the root `services/api` backend *calls into* it rather than the capstone living inside `services/api/app/`.
  Cleaner separation for grading. Still **reuse** the root WSL-Hermes task runner and the React UI
  rather than rebuilding them.
- **Flywheel storage = Parquet + files.** Inference telemetry → columnar **Parquet** files
  (partitioned by date/model); the model registry and dataset-snapshot metadata → **JSON/YAML** files.
  No database server. The root app's in-memory stores are not used for persistence.
- **Scope = implemented (focus: decision fusion + data flywheel).** `orchestration/` and `flywheel/`
  are built under `src/capstone/` and runnable offline. Retrain is simulated (`flywheel/trainer.py`)
  per "模型先不下载"; swap `_simulate_metrics` for real 大作业1/2 training (via the root WSL-Hermes
  async task pattern) when downloading/training is unblocked — the pipeline interface stays the same.

The capstone is the **brain** the root `services/api` + `apps/web` demo becomes once its
`DecisionService` stub is upgraded (→ LLM) and the flywheel is added.

## Common commands

Offline-runnable (no model download). Set `PYTHONIOENCODING=utf-8` if the GBK console garbles Chinese.

```powershell
# 前置：大作业3 知识库（dialog_rag 适配器 + 决策解释需要）
cd ..\大作业3 ; python scripts\2_build_kb.py ; cd ..\期末作业

python scripts\run_pipeline.py                          # 端到端决策（融合+解释），落遥测
python scripts\simulate_flywheel.py                     # 飞轮闭环：提升曲线 + 门控拦截 + 回滚
python scripts\trigger_retrain.py --model detection     # 手动一轮重训（门控晋升/保留）
python scripts\trigger_retrain.py --model detection --inject-regression  # 演示门控拦截劣化候选
python scripts\serve.py                                 # Web 仪表盘 -> http://127.0.0.1:8002
```

Web 界面：`src/capstone/api.py`（FastAPI，端点 `/api/decide` · `/api/flywheel/{seed,round}` ·
`/api/registry/{model}`）+ `web/index.html`（决策驾驶舱 + 数据飞轮面板，单文件零构建）。

Entrypoints live in `pipeline.py`: `TrafficDecisionSystem.decision_flow(scene)` and
`.flywheel_round(model_name)`. Both share the same telemetry store + model registry.

For reused small models, the real (training) commands already exist in the sibling folders:
- Forecasting (大作业1): `python train.py -d <METRLA|PEMS04|...> -g <gpu_id>` (PyTorch ≥ 1.11).
- Detection (大作业2): `python train.py --config configs/experiments/yolo11n_tt100k.yaml`,
  plus `val.py` / `predict.py`. See `大作业2/CLAUDE.md` for the full set.
- Travel Q&A (大作业3): **implemented and runnable offline** — `python scripts/2_build_kb.py`
  then `python scripts/chat.py --demo`; the `TravelQAApp.ask()` orchestrator + intent router are
  reusable as the capstone's dialog/orchestration entry. See `大作业3/CLAUDE.md`.

## What future Claude instances should verify before acting

Locked: integration path = standalone package; storage = Parquet+files; decision fusion + flywheel
are implemented and runnable offline.

Still open — confirm before extending:

1. **Real retrain vs simulation.** `flywheel/trainer.py` currently simulates metric gains
   (per "模型先不下载"). Before wiring real STAEformer/YOLO retraining, confirm compute + cadence and
   keep the `retrain_candidate` interface stable.
2. **Big-model provider** — 大作业3 already has a pluggable LLM provider (offline / OpenAI-compatible
   DeepSeek). Reuse it, or switch to root `config.py`'s OpenAI config / the WSL-Hermes agent? Confirm
   which is the "big model" for decisions vs. report generation.
3. **Retrain cadence & compute** — scheduled vs. threshold-triggered; is there a GPU box for STAEformer
   / YOLO retraining, and where does it run (Windows / WSL2 / remote)?
4. **Human-in-the-loop** — is labeling fully automated (LLM), or is there a review step / UI?
5. **Scope of 大作业3 integration** — use its `TravelQAApp` as the dialog/orchestration entry (recommended;
   router + RAG already exist), or only reuse its knowledge base + tools and write orchestration anew?
   Are Q&A logs a live flywheel data source?
6. **Report deliverable** — like the siblings, this likely needs a written report; confirm format and
   whether it reuses `大作业2`'s LaTeX template (`课程设计模版_2026年/`).

## Conventions

- Project paths and report prose are in Chinese; code identifiers and this guidance file are in English,
  matching `大作业2/CLAUDE.md` and `大作业3/CLAUDE.md`.
- Prefer configuring thresholds, schedules, and model paths via YAML config over hardcoding in scripts.
- Keep files focused (~200–400 lines, 800 max) and organize by feature/domain.
- Reuse the root app's manual dependency wiring style (`services/api/app/dependencies.py`,
  module-level singletons) if extending it.
- **Verify the installed Dify / DeepSeek / LLM / training API surface against current docs (Context7 /
  vendor) before writing integration code** — do not assume APIs from training data.
