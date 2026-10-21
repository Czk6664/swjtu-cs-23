# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository scope

This is **大作业3 — 大小模型协同的智能交通出行问答系统** (a big-small model collaborative
intelligent-transportation *travel Q&A* system). It is a **self-contained homework sub-repo** inside
the `智能交通` course directory; it builds independently of the root app (`apps/`, `services/`) and the
other homework folders.

> **Note:** An earlier draft of this assignment was an *embodied robot-dog traffic-duty* project
> (Isaac Sim). That direction has been **dropped**. The robot dog is no longer part of 大作业3 —
> ignore any robot-dog / Isaac references that still linger in `期末作业/` docs; those are stale and
> should be reconciled to this Q&A system.

The prototype is **implemented and runnable offline** (see "Project structure" / "Common commands"
below). Current stage per the user's constraint is **"模型先不下载"**: the full
抓取→知识库→意图路由→检索/工具→可溯源回答 chain runs without downloading any model (offline LLM
+ hash embedder), and the 大作业1/2 integrations read those homeworks' real outputs. Hooking up the
real DeepSeek base model + fine-tuning is config-gated and deferred.

## What this assignment is

A retrieval-augmented, fine-tuned **travel knowledge Q&A prototype** for Chengdu, built on the
**Dify** application framework with a **DeepSeek open-source 1–7B** model as the base.

### Base requirements (基础要求 — mandatory)

1. **Framework:** build on the **Dify** development framework.
2. **Base model:** use a **DeepSeek open-source 1–7B** model as the foundation model (基座模型).
3. **Knowledge corpus:** **web-scrape the Chengdu Traffic Management Bureau (成都市交管局) website
   information-bulletin board** (信息发布栏) and build a **local RAG travel knowledge base** from it.
4. **Fine-tuning:** **fine-tune the base model** on travel/traffic-domain data.
5. **Prototype features (功能):**
   - 交管信息问答 — traffic-administration info Q&A (driven by the RAG knowledge base)
   - 天气问答 — weather Q&A
   - 出行建议 — travel advice
   - 出行路径规划 — trip route planning
6. **Deliverable:** a complete homework **report** (作业报告).

### Optional "pick-one" extension (三选一要求 — optional)

Integrate the model results from the first two assignments to demonstrate:
- 交通流预测问答 — traffic-flow *forecasting* Q&A, reusing **大作业1** (STAEformer forecasting), and/or
- 交通目标识别理解问答 — traffic-object *detection* understanding Q&A, reusing **大作业2** (YOLO / TT100K).

This is the "big-small model collaboration" angle: the LLM (big model) answers in natural language by
**calling / interpreting the structured outputs of the small specialist models** rather than re-deriving
them.

## Parent / sibling context (what can be reused)

| Path | What it is | Reuse for 大作业3 |
|------|------------|-------------------|
| `大作业1` | STAEformer traffic-flow **forecasting** (PyTorch). Produces `results/*.json` metrics. | Optional extension: forecasting-Q&A tool the LLM can call. |
| `大作业2` | YOLO / TT100K traffic-sign **detection**. Has a LaTeX report template + experiment framework. | Optional extension: detection-understanding Q&A; **report LaTeX template** (`课程设计模版_2026年/`) can be reused for this assignment's report. |
| repo root | FastAPI backend with OpenAI config wired + React frontend. | Reference only — this assignment runs standalone on Dify, not on the root app. |

Do **not** build on the root app's `services/api` unless explicitly asked; this is a separate Dify-based
deliverable.

## Architecture (intended)

```
              ┌─────────────────────────── Dify app ────────────────────────────┐
  user query  │   ┌──────────┐    ┌─────────────┐    ┌────────────────────────┐ │
 ───────────► │   │  Router   │──► │ RAG retrieve │──► │ DeepSeek 1–7B (微调后) │ │ ──► answer
              │   └──────────┘    │  (本地知识库) │    └────────────────────────┘ │
              │        │          └─────────────┘              ▲                  │
              │        │ tool call                             │ context          │
              │        ▼                                       │                  │
              │   ┌──────────────────────────────────────────┐                   │
              │   │ external/structured tools:                │                   │
              │   │  • weather API           (天气问答)        │                   │
              │   │  • route planning API    (路径规划)        │                   │
              │   │  • 大作业1 forecasting   (optional)        │                   │
              │   │  • 大作业2 detection      (optional)        │                   │
              │   └──────────────────────────────────────────┘                   │
              └──────────────────────────────────────────────────────────────────┘
                          ▲
            ┌─────────────┴──────────────┐
            │ scraper → 成都市交管局信息发布栏 │  (offline ingestion → chunk → embed → vector store)
            └────────────────────────────┘
```

- The **base model is small** (1–7B) and answers cheaply/locally.
- The **knowledge base is local RAG** — answers about 交管信息 are grounded in scraped, cited bulletins,
  not the model's parametric memory.
- **Weather / route planning / forecasting / detection** are **tools** the app routes to; the model
  composes the natural-language answer around their structured results.

## Project structure (implemented)

```
大作业3/
├── src/travelqa/        # 核心库
│   ├── config.py        # 配置(env > config.yaml > 默认)；密钥只走环境变量
│   ├── scraper/         # 成都交管发布栏抓取 + 内置离线样例语料(sample_corpus.py)
│   ├── kb/              # chunk → embed(可插拔) → 纯 Python 向量库(store.py) → build
│   ├── llm/             # provider 抽象: offline 模板应答 / openai_compatible(DeepSeek)
│   ├── tools/           # weather · route · forecast(大作业1) · detection(大作业2)
│   ├── router.py        # 六类意图关键词路由 (Intent 枚举)
│   ├── rag.py           # 检索 + 带来源证据组织
│   └── app.py           # TravelQAApp.ask(query) -> Answer  ← 端到端编排器
├── scripts/             # 1_scrape.py · 2_build_kb.py · chat.py(--demo / -q)
├── finetune/            # build_dataset.py · train_lora.py(默认 dry-run) · lora_config.yaml
├── dify/                # app.dsl.yaml + README(Dify 集成说明)
├── eval/                # eval_set.jsonl + run_eval.py(意图路由/关键信息命中)
├── report/report.md     # 作业报告骨架
├── data/                # raw(抓取产物) / kb(向量索引)  ← 运行后生成，已 gitignore
├── config.example.yaml  # 复制为 config.yaml 后改
└── requirements.txt
```

## Common commands

> 原型默认**全离线**(`llm.provider=offline`, `embedding.provider=offline_hash`)，
> **不下载/不调用任何大模型**即可端到端跑通。接真实 DeepSeek/语义向量见 README。
> 控制台中文乱码时设 `PYTHONIOENCODING=utf-8`(文件本身是 UTF-8，仅 GBK 终端显示问题)。

```powershell
pip install -r requirements.txt          # 抓取/配置依赖；纯离线问答用标准库即可
python scripts/1_scrape.py --offline     # 抓取(无网络回退内置样例) -> data/raw
python scripts/2_build_kb.py             # 构建 RAG 知识库 -> data/kb/index.json
python scripts/chat.py --demo            # 演示六类意图
python eval/run_eval.py                  # 离线评测(当前 12/12 路由, 7/7 命中)
python scripts/serve.py                  # Web 界面 -> http://127.0.0.1:8001 (FastAPI + web/index.html)
python finetune/build_dataset.py         # 生成 SFT 数据 finetune/data/sft.jsonl
python finetune/train_lora.py            # dry-run：仅校验，不下载/不训练
python finetune/train_lora.py --run      # 真正微调(下载模型+占显存；先装 torch/peft 等)
```

报告若用 LaTeX：复用 `大作业2/课程设计模版_2026年/`，`xelatex → bibtex → xelatex × 2`。

## Conventions / things to verify before acting

- **"模型先不下载" 是当前约束**：保持离线可跑；新增能力要有离线兜底，不要让默认路径依赖模型下载。
- **小模型只接不重训**：forecast/detection 工具读 `大作业1/results/*.json`、`大作业2/.../results.csv` +
  `tt100k.yaml`，不要在此重新训练那两个模型。`summarize()` 缺文件时返回 `available=False`，勿抛异常。
- **可插拔点**：embedder(`kb/embed.py`)、LLM(`llm/provider.py`) 都按 provider 切换，接真实模型时
  只改配置 + 实现类，不动编排逻辑。
- **Verify the live API surface** of Dify, DeepSeek, the embedding model, and any weather/route API
  against current docs before implementing — versions drift.
- **Secrets:** never hardcode API keys (weather, route planning, model endpoints). Use env vars / a
  Dify-managed credential, per the global security rules.
- **Scraping etiquette:** the 成都市交管局 site is a government source — respect robots.txt, throttle
  requests, cache raw HTML, and keep provenance (URL + fetch date) so RAG answers can cite sources.
- **Grounding & citations:** 交管信息 answers must be traceable to scraped bulletins; surface the
  source so the answer is verifiable rather than hallucinated.
- **Optional extension reuses, not reimplements:** if doing the 三选一 part, call 大作业1 / 大作业2
  outputs as tools — don't retrain those models here.
- **Report:** the LaTeX report template lives in `大作业2/课程设计模版_2026年/`; reuse it for consistency.
