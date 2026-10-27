# 期末作业

<!-- directory-guide:start -->
## 本层内容介绍

这里是“智能+交通”课程下的“期末作业”目录，主要用于整理该项课程实践的相关材料，具体内容见下方文件与子目录。

**阅读建议：**先读任务或报告了解目标，再看代码、数据和结果；借鉴方法后独立完成自己的任务。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **37 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

| 子目录 | 内容与用途 |
| --- | --- |
| [configs](configs/README.md) | 运行或实验配置文件 |
| [data](data/README.md) | 项目使用的数据或样例输入 |
| [scripts](scripts/README.md) | 处理数据、生成材料或辅助运行的脚本工具 |
| [src](src/README.md) | 程序源代码与实现文件 |
| [web](web/README.md) | 项目的应用或界面相关文件 |

- **配置及其他配套文件（1 份）**：[.gitignore](.gitignore)。
- **文档与说明（2 份）**：[CLAUDE.md](CLAUDE.md)、[design.md](design.md)。

<!-- directory-guide:end -->

所属课程：[智能+交通](../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [configs/](configs/README.md)
- [data/](data/README.md)
- [scripts/](scripts/README.md)
- [src/](src/README.md)
- [web/](web/README.md)
- [.gitignore](.gitignore)
- [CLAUDE.md](CLAUDE.md)
- [design.md](design.md)

[返回上级目录](../README.md)

## 原有项目说明

# 期末作业 — 大小模型协同的智能交通管理决策系统

把本课程三个大作业整合为一个**可持续自我优化**的完整系统，聚焦两个核心新增能力：
**决策融合**（大小模型协同）与**数据飞轮**（让模型越用越准、可观测、可回滚）。

> 设计文档见 [`design.md`](design.md)。本目录已从设计阶段进入**可运行实现**。
> 当前遵循"模型先不下载"：全链路离线可跑通，重训为确定性模拟（演示闭环/门控/回滚机制）。

## 整合关系
| 来源 | 角色 | 复用方式 |
|------|------|----------|
| 大作业1 STAEformer | 小模型·交通流预测 | 读 `results/*.json`（真实 MAE/RMSE/MAPE） |
| 大作业2 YOLO/TT100K | 小模型·交通标志检测 | 读 `results.csv` + `tt100k.yaml`（真实 mAP50/类别） |
| 大作业3 出行问答 | 大模型层载体·NL接口+RAG | 复用 `travelqa`（意图路由 / RAG / LLM provider） |

## 两个核心
### 1. 决策融合（`src/capstone/orchestration/`）
路由 → 小模型推理 → **加权置信融合**成统一态势（风险分+等级+归因）→ 决策（建议动作 +
可解释理由 + 自然语言解释）。同时检测"大小模型分歧"作为飞轮高价值难例。
替换了根 `services/api` 的规则桩 `DecisionService`。

### 2. 数据飞轮（`src/capstone/flywheel/`）
```
采集(Parquet) → 难例挖掘 → 策展标注(版本化快照) → 重训(候选) → 门控评估 → 晋升/保留 → 监控
```
- **采集** `collector.py`：每次推理落 Parquet（按 模型/日期 分区，字段见 design.md）。
- **挖掘** `miner.py`：低置信 / 协同分歧 / 误差超阈 / 检索未命中。
- **标注** `labeler.py`：自动标注 + 版本化数据集快照（manifest 可复现）。
- **重训** `trainer.py`：触发候选（当前为确定性模拟；接口可换真实训练）。
- **门控** `evaluator.py`：主指标提升达标且安全子集不回归才晋升，否则保留生产版本。
- **注册表** `registry.py`：版本/状态管理，一键回滚。

## 快速开始（离线，无需下载模型）
```powershell
# 前置：大作业3 知识库（供 dialog_rag / 解释使用）
cd ..\大作业3 ; python scripts\2_build_kb.py ; cd ..\期末作业

# 1) 一次端到端决策（路由→小模型→采集→融合→决策与解释）
python scripts\run_pipeline.py

# 2) 数据飞轮闭环演示（提升曲线 + 门控拦截劣化候选 + 可回滚）
python scripts\simulate_flywheel.py

# 3) 手动触发一轮重训
python scripts\trigger_retrain.py --model detection
python scripts\trigger_retrain.py --model detection --inject-regression
```
> 控制台中文乱码时设 `PYTHONIOENCODING=utf-8`（文件为 UTF-8，仅 GBK 终端显示问题）。

## Web 界面（单文件前端 + FastAPI）
```powershell
cd ..\大作业3 ; python scripts\2_build_kb.py ; cd ..\期末作业   # 前置知识库
python scripts\serve.py         # -> http://127.0.0.1:8002  浏览器打开即用
```
- 后端 `src/capstone/api.py`：`/api/decide`、`/api/flywheel/seed|round`、`/api/registry/{model}`，托管 `web/index.html`。
- 前端 `web/index.html`：**决策驾驶舱**（场景输入→风险环形图+信号贡献条+融合理由）+
  **数据飞轮面板**（灌难例→跑飞轮→指标提升曲线 canvas + 版本注册表 + 门控日志）。
- 需要 `fastapi`、`uvicorn`（环境已具备；否则 `pip install fastapi uvicorn`）。

## 验证过的效果
- 决策融合：三类信号按权重+置信融合，输出可解释归因（实测见 `run_pipeline.py`）。
- 飞轮提升曲线：detection mAP50 随轮次 `0.758 → 0.773 → 0.793 → 0.814`（从大作业2 真实基线起）。
- 门控负例：劣化候选被拦截，生产版本不变、保留回滚（实测见 `simulate_flywheel.py`）。

## 目录
```
期末作业/
├── src/capstone/
│   ├── models/          # 小模型适配器: forecast(大1) / detection(大2) / dialog_rag(大3)
│   ├── orchestration/   # router · fusion · decision  ← 决策融合
│   ├── flywheel/        # collector · miner · labeler · trainer · evaluator · registry
│   ├── pipeline.py      # TrafficDecisionSystem: decision_flow / flywheel_round
│   └── config.py
├── configs/thresholds.yaml
├── scripts/             # run_pipeline · simulate_flywheel · trigger_retrain
├── data/                # telemetry(Parquet) / snapshots / registry  ← 运行后生成，gitignore
├── design.md
└── README.md
```

## 接入真实能力（后续）
- **真实大模型**：把大作业3 的 `llm.provider` 切到 `openai_compatible` 指向微调后的 DeepSeek。
- **真实重训**：把 `flywheel/trainer.py` 的 `_simulate_metrics` 换成调用大作业1/2 训练脚本，
  用根 WSL-Hermes 异步任务承载长任务，接口不变。
- **接根应用**：根 `services/api` 的 `analyze-scene` 转发到本包 `decision_flow`，替换 `DecisionService` 桩。

