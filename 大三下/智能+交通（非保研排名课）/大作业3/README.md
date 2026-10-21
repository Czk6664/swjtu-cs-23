# 大作业3

所属课程：[智能+交通](../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [ab_eval_v4/](ab_eval_v4/README.md)
- [autodl/](autodl/README.md)
- [course_design_2026/](course_design_2026/README.md)
- [data/](data/README.md)
- [deepseek_lora__v4/](deepseek_lora__v4/README.md)
- [deploy/](deploy/README.md)
- [dify/](dify/README.md)
- [docs/](docs/README.md)
- [eval/](eval/README.md)
- [finetune/](finetune/README.md)
- [report/](report/README.md)
- [scripts/](scripts/README.md)
- [src/](src/README.md)
- [web/](web/README.md)
- [成都市公安局_files/](%E6%88%90%E9%83%BD%E5%B8%82%E5%85%AC%E5%AE%89%E5%B1%80_files/README.md)
- [课程设计模版_2026年/](%E8%AF%BE%E7%A8%8B%E8%AE%BE%E8%AE%A1%E6%A8%A1%E7%89%88_2026%E5%B9%B4/README.md)
- [.gitignore](.gitignore)
- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)
- [config.example.yaml](config.example.yaml)
- [config.yaml](config.yaml)
- [ppt_generation_prompts.md](ppt_generation_prompts.md)
- [requirements.txt](requirements.txt)
- [setup.ps1](setup.ps1)
- [setup_semantic_rag.ps1](setup_semantic_rag.ps1)
- [start_web.ps1](start_web.ps1)
- [成都市公安局.html](%E6%88%90%E9%83%BD%E5%B8%82%E5%85%AC%E5%AE%89%E5%B1%80.html)
- [智能交通作业三ppt.pptx](%E6%99%BA%E8%83%BD%E4%BA%A4%E9%80%9A%E4%BD%9C%E4%B8%9A%E4%B8%89ppt.pptx)

[返回上级目录](../README.md)

## 原有项目说明

# 大作业3 — 大小模型协同的智能交通出行问答系统

基于 **Dify** 框架、以 **DeepSeek 1–7B** 为基座模型，结合**本地 RAG 出行知识库**（网络采集成都市
交管局信息发布栏）与**微调**，实现出行知识问答原型；并完成**高阶要求**——集成大作业1（交通流预测）
与大作业2（交通目标识别）成果，支持交通流预测问答与交通标志识别理解问答。

## 技术路线：Hybrid-RAG 混合检索增强生成

本系统采用 **Hybrid Search + Rerank** 的 RAG 架构，兼顾语义理解与关键词精确匹配：

```
成都交管局信息发布栏
      ↓
网页采集与清洗 → 按公告结构分块(标题/时间/正文/路段)
      ↓
BGE-M3 向量化 ──┐
                 ├─→ Hybrid Search 混合检索(向量 + BM25)
BM25 关键词索引 ─┘
      ↓
bge-reranker-v2-m3 重排序
      ↓
DeepSeek 1.5B/7B 生成可溯源回答
      ↓
交通问答 / 天气 / 出行建议 / 路径规划
```

### 为什么用 Hybrid Search 而不是纯向量检索

交通出行问答依赖**具体路名、日期、政策关键词、公告标题**，纯向量检索容易语义漂移。
例如"二环高架今日限行"需要精确命中含"二环高架""限行"的公告，而非语义相近但无关的内容。

| 方法 | 速度 | 精准度 | 适合本项目 |
|------|------|--------|-----------|
| 普通向量 RAG | 快 | 中等 | 一般（易漏路名/日期） |
| BM25 关键词检索 | 很快 | 中等 | 不够（语义弱） |
| **Hybrid Search + Rerank** | **较快** | **高** | **最合适** |
| GraphRAG | 慢 | 高 | 不推荐主线（实现成本高） |

### 大小模型协同

| 模块 | 模型/工具 | 作用 |
|------|----------|------|
| 意图识别 | 关键词路由 / Dify 分类器 | 判断交管问答/天气/路径/建议/预测/识别 |
| 知识检索 | BGE-M3 + BM25 → Hybrid Search | 向量语义召回 + 关键词精确匹配 |
| 重排序 | bge-reranker-v2-m3 | 提高召回片段相关性 |
| 回答生成 | DeepSeek 7B | 自然语言答案 |
| 简单问答 | DeepSeek 1.5B | 轻量级政策问答 |
| 天气 | 天气 API | 实时天气 |
| 路径规划 | 地图 API / 规则模块 | 路线建议 |
| 可选扩展 | 大作业1 STAEformer | 交通流预测 |
| 可选扩展 | 大作业2 YOLO/TT100K | 交通标志识别 |

## 功能覆盖
| 功能 | 意图 | 实现 |
|------|------|------|
| 交管信息问答 | `traffic-info` | Hybrid RAG（成都交管发布栏知识库） |
| 出行建议 | `travel-advice` | Hybrid RAG + 规则 |
| 天气问答 | `weather` | 天气工具（mock / 高德 API） |
| 出行路径规划 | `route` | 路径工具（mock / 高德 API） |
| 交通流预测问答（高阶） | `forecast` | 读取大作业1 `results/*.json` |
| 交通标志识别理解（高阶） | `detection` | 读取大作业2 `tt100k.yaml` + `results.csv` |

## 快速开始（离线，无需下载任何模型）
```powershell
pip install -r requirements.txt          # 仅抓取/配置需要；离线问答用标准库即可
python scripts/1_scrape.py --offline     # 抓取成都交管发布栏(无网络则用内置样例语料)
python scripts/2_build_kb.py             # 构建 RAG 知识库 -> data/kb/index.json
python scripts/chat.py --demo            # 演示六类意图
python eval/run_eval.py                  # 离线评测(意图路由 + 关键信息命中)
```

交管官网出现防自动化页面时，按 [`docs/traffic_bulletin_collection.md`](docs/traffic_bulletin_collection.md)
人工审核公告原文，再运行 `python scripts/import_bulletins.py` 导入真实语料。对于
`cdgaj.chengdu.gov.cn` 公示公告栏目，也可把浏览器保存的 HTML 放入
`data/manual/cdgaj_html/`，运行 `python scripts/import_saved_cdgaj.py` 批量解析。
> 默认 `config.example.yaml` 中 `llm.provider=offline`、`embedding.provider=offline_hash`、
> `retrieval.mode=hybrid`，**不下载/不调用任何大模型**即可端到端跑通。
> Hybrid Search 中向量检索用离线哈希词袋，BM25 用纯 Python TF-IDF，Reranker 离线时跳过。

## Web 界面（单文件前端 + FastAPI）
```powershell
python scripts/2_build_kb.py    # 先建知识库
python scripts/serve.py         # -> http://127.0.0.1:8001  浏览器打开即用
```
- 后端 `src/travelqa/api.py`：`POST /api/ask`、`GET /api/health`，并托管 `web/index.html`。
- 前端 `web/index.html`：零构建对话界面，显示意图徽章、来源引用、工具/模型结构化结果。

本机 Ollama 已导入 `travelqa` 模型时，将 `config.yaml` 中 `llm.provider` 设为
`ollama_native`、`base_url` 设为 `http://127.0.0.1:11434`，然后可直接运行：

```powershell
.\start_web.ps1
```

原生 Ollama provider 会固定发送 `think=false`，网页只展示最终回答。

完整运行包首次解压后，可运行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
.\start_web.ps1
```

## 接入高德天气与路径规划 API
1. 登录[高德开放平台控制台](https://console.amap.com/dev/key/app)，创建应用和
   `Web 服务` 类型 Key。天气查询、地理编码和路径规划共用这一个 Key。
2. 复制 `config.example.yaml` 为 `config.yaml`，把 `tools.weather.provider` 和
   `tools.route.provider` 都改成 `amap`。
3. 在启动 Web 服务的同一个 PowerShell 会话中设置 Key，再运行程序：

```powershell
$env:TRAVELQA_AMAP_KEY = "你的高德 Web 服务 Key"
python scripts/test_amap_tools.py
python scripts/serve.py
```

需要长期保存时，可执行 `setx TRAVELQA_AMAP_KEY "你的高德 Web 服务 Key"`，然后重新打开
PowerShell。也可以将 `TRAVELQA_AMAP_KEY=...` 写入项目根目录下被 Git 忽略的
`.env.local`，便于离线演示机随项目使用。密钥不要写入 YAML 或提交到仓库。天气查询默认使用成都行政区划代码
`510100`；路径规划会优先调用 POI 搜索 API，把“成都东站”等名称转换为入口经纬度，
搜索不到时再回退到地理编码 API，然后规划路线。
真实模式请求失败时会返回 `available=false`，不会使用 mock 数值冒充实时结果。

交通法规文件可放入 `data/raw/open_data/`，支持 Markdown、DOCX 和 PDF。导入并重建 RAG：

```powershell
python scripts/import_regulations.py
python scripts/2_build_kb.py
```

启用语义 RAG 时，`config.yaml` 使用 `BAAI/bge-m3 + BM25 + BAAI/bge-reranker-v2-m3`。
首次运行会从魔搭社区下载 safetensors 权重到项目内 `models/rag/`：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_semantic_rag.ps1
.\start_web.ps1
```

## 接入真实模型（可选，需联网/部署）
1. 复制 `config.example.yaml` 为 `config.yaml`。
2. 部署或购买 DeepSeek 的 OpenAI 兼容接口（如 `vllm serve deepseek-ai/deepseek-llm-7b-chat`）。
3. 改 `llm.provider: openai_compatible`，设 `base_url`/`model`，密钥用环境变量 `TRAVELQA_LLM_API_KEY`。
4. 语义向量切换 `embedding.provider: sentence_transformers`，`model: BAAI/bge-m3`。
5. 启用 Reranker：`retrieval.reranker.provider: sentence_transformers`，`model: BAAI/bge-reranker-v2-m3`。

### 推荐技术栈（接入真实模型时）

| 层级 | 推荐方案 |
|------|---------|
| 开发框架 | Dify |
| 基座模型 | DeepSeek 1.5B / 7B |
| Embedding | BAAI/bge-m3 |
| Reranker | BAAI/bge-reranker-v2-m3 |
| 检索方式 | Hybrid Search（向量 + BM25） |
| 知识库 | Dify Knowledge Base / 本地向量库 |
| 天气 | 高德天气 API / 和风天气 API |
| 路径规划 | 高德地图 API / 百度地图 API |
| 微调方式 | LoRA / QLoRA |

## 微调 DeepSeek（数据已就绪，按要求暂不下载模型）
```powershell
python finetune/build_dataset.py         # 生成 SFT 全量数据 + train/val 划分 + stats
python finetune/train_lora.py            # dry-run：只校验，不下载/不训练
python finetune/train_lora.py --run      # 真正训练(会下载模型、占显存；需先装 torch/peft 等)
```

微调目标：让模型学会交通问答格式、出行建议表达、根据检索资料回答（而非背公告）。
公告知识放在 RAG 里，微调只优化表达方式。

生成文件位于 `finetune/data/`：`sft.jsonl` 为全量 Alpaca 格式样本，
`train.jsonl` / `val.jsonl` 为训练和验证划分，`stats.json` 记录类别分布。
结构化样本来自 `data/raw/open_data/` 中归档的成都公共开放交通数据。
生成器还会加入少量工具调用、工具结果解释、工具不可用和拒答样本。天气与路径规划
示例只训练“先调用工具”或“严格解释已给结果”，不会把离线 mock 数值批量当成事实。
同一事实或工具场景使用 `group_id` 整组切分，避免释义变体泄漏到验证集；构建时还会
拒绝包含 `None`、占位公告 URL 或无工具结果支撑的路线与天气答案。

## Dify 集成
见 [`dify/README.md`](dify/README.md) 与 [`dify/app.dsl.yaml`](dify/app.dsl.yaml)：把同一套知识库与工具
搬到 Dify 的可视化编排上。

## 目录
```
大作业3/
├── src/travelqa/        # 核心库: scraper / kb / llm / tools / router / rag / app
├── scripts/             # 1_scrape · 2_build_kb · chat（演示）
├── finetune/            # SFT 数据构造 + DeepSeek (Q)LoRA 训练脚本 + 配置
├── dify/                # Dify 应用 DSL 与集成说明
├── eval/                # 评测集 + 离线评测脚本
├── report/              # 作业报告
├── data/                # raw(抓取产物) / kb(向量索引)  ← 运行后生成
├── config.example.yaml
└── requirements.txt
```

## 说明
- 当前为「模型先不下载」阶段：离线模式可完整演示**抓取→知识库→意图路由→Hybrid 检索/工具→可溯源回答**
  的全链路，以及大作业1/2 的真实结果接入；接入真实 DeepSeek + BGE-M3 + Reranker + 微调后即为完整产品形态。
- Hybrid Search 默认开启：向量检索（离线哈希 / BGE-M3）+ BM25 关键词检索，RRF 融合排序。
- 内置样例语料为课程演示用途，正式部署应由 scraper 抓取实时公告替换，并遵守站点 robots 与限速。

