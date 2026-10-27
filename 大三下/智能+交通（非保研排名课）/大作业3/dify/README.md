# dify

<!-- directory-guide:start -->
## 本层内容介绍

这里是“智能+交通”课程下的“dify”目录，主要用于整理该主题的文档与参考材料。

**阅读建议：**先根据下方文件名选择相关文档，再结合上级介绍理解背景；原文件中的说明优先。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **4 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

- **文档与说明（1 份）**：[DIFY_1_14_WORKFLOW.md](DIFY_1_14_WORKFLOW.md)。
- **配置及其他配套文件（2 份）**：[app.dsl.yaml](app.dsl.yaml)、[travelqa-tools.openapi.yaml](travelqa-tools.openapi.yaml)。
- **代码与脚本（1 份）**：[setup_dify_1_14.ps1](setup_dify_1_14.ps1)。

<!-- directory-guide:end -->

所属课程：[智能+交通](../../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [app.dsl.yaml](app.dsl.yaml)
- [DIFY_1_14_WORKFLOW.md](DIFY_1_14_WORKFLOW.md)
- [setup_dify_1_14.ps1](setup_dify_1_14.ps1)
- [travelqa-tools.openapi.yaml](travelqa-tools.openapi.yaml)

[返回上级目录](../README.md)

## 原有项目说明

# Dify 集成说明

本目录把原型对接到 **Dify** 框架，满足作业「基于 Dify 开发框架」的要求。

> 已适配你下载的 `dify-1.14.2.zip`。实际落地步骤见
> [`DIFY_1_14_WORKFLOW.md`](DIFY_1_14_WORKFLOW.md)：
> `setup_dify_1_14.ps1` 启动 Dify，`travelqa-tools.openapi.yaml` 作为自定义 API 工具导入 Dify。

## 为什么需要 Dify
Dify 提供可视化的对话编排、知识库(RAG)、模型接入与工具节点。本项目把：
- **基座模型** → DeepSeek 1-7B（在 Dify「模型供应商」中配置，或指向本地 vLLM/Ollama 的 OpenAI 兼容端点）
- **RAG 知识库** → `data/kb`（由 `scripts/2_build_kb.py` 用抓取的成都交管发布栏构建）
  - **检索方式** → Hybrid Search（向量检索 + 全文关键词检索），Dify 原生支持
  - **Embedding** → BGE-M3（中文/长文本/混合检索，Dify 知识库设置中选择）
  - **Reranker** → bge-reranker-v2-m3（Dify 知识库设置中开启 Rerank）
- **工具** → 天气 / 路径规划 / 交通流预测(大作业1) / 交通标志识别(大作业2)
- **意图路由** → `question-classifier` 节点（对应 `src/travelqa/router.py` 的六类意图）

## 部署步骤（概览）
1. 自建 Dify（官方 `docker compose up -d`）。
2. 在「模型供应商」配置 DeepSeek：
   - 用官方 API，或本地部署 `vllm serve deepseek-ai/deepseek-llm-7b-chat`（微调后换成合并 LoRA 的模型）。
3. 创建「知识库」`chengdu-traffic-kb`，上传由本仓库抓取/构建的文档（`data/raw/documents.json` 或导出的纯文本）。
   - 索引方式选 **High Quality**
   - 检索方式选 **Hybrid Search**（向量 + 全文关键词，RRF 融合）
   - Embedding 模型选 **BAAI/bge-m3**
   - 开启 **Rerank**，模型选 **BAAI/bge-reranker-v2-m3**
   - TopK 设 8~10，Rerank TopK 设 4~6
4. 新建「Chatflow / Advanced Chat」应用，导入 `app.dsl.yaml`（或按其结构手动搭节点）。
5. 工具节点：用 HTTP 节点调用本项目封装的工具（见 `src/travelqa/tools/`），或在 Dify 内置工具中等价配置。

> 说明：`app.dsl.yaml` 是结构蓝图，不同 Dify 版本的 DSL 字段会有差异，导入前请对照你所部署版本的导出样例核对字段。

## 本地原型 vs Dify
- 本仓库的 `scripts/chat.py` 是**不依赖 Dify、可离线跑通**的等价编排，便于开发/评测/答辩演示。
- Dify 版本用于交付「可视化、可运营」的产品形态。两者共用同一套知识库与工具逻辑。
- 本地原型已实现 Hybrid Search（向量 + BM25）+ Reranker，Dify 中等价配置即可保持一致。

