# Dify 1.14.2 落地流程

本项目现在按“Dify 编排 + 本地 TravelQA 工具服务”的方式使用 Dify：

```text
Dify Advanced Chat / Chatflow
  -> question-classifier 意图分类
  -> Knowledge Retrieval / HTTP Tool
  -> LLM 节点组织回答

TravelQA FastAPI
  -> /api/tools/weather
  -> /api/tools/route
  -> /api/tools/forecast/predict
  -> /api/tools/detection/summary
  -> /api/ask
```

## 1. 启动 TravelQA 工具服务

```powershell
cd D:\大三下\智能交通\大作业3
.\start_web.ps1
```

确认：

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/health
```

## 2. 启动 Dify 1.14.2

你已经下载了：

```text
D:\大三下\智能交通\大作业3\dify-1.14.2.zip
```

运行：

```powershell
cd D:\大三下\智能交通\大作业3
.\dify\setup_dify_1_14.ps1
```

启动后打开：

```text
http://localhost
```

## 3. 在 Dify 中导入工具

进入 Dify 控制台：

```text
工具 -> 自定义工具 -> OpenAPI / Swagger 导入
```

导入：

```text
dify/travelqa-tools.openapi.yaml
```

如果 Dify 跑在 Docker Desktop 里，工具地址使用：

```text
http://host.docker.internal:8001
```

如果 Dify 与 TravelQA 在同一网络命名空间，才使用：

```text
http://127.0.0.1:8001
```

## 4. 建 Dify Chatflow

推荐节点：

```text
Start
  -> Question Classifier
       交管信息 / 出行建议 -> Knowledge Retrieval -> LLM
       天气 -> weatherQuery -> LLM
       路径规划 -> routePlan -> LLM
       交通流预测 -> forecastPredict -> LLM
       交通标志识别 -> detectionSummary -> LLM
```

LLM 节点提示词建议：

```text
你是成都智能交通出行问答助手。只能基于上游知识库片段或工具 JSON 结果回答。
如果工具返回 available=false，必须说明当前工具不可用或数据不足，不能编造数值。
交管公告类回答必须给出可核验来源；天气、路线、预测和识别结果必须说明数据来源与局限性。
```

## 5. 大作业1真实预测

`forecastPredict` 会尝试加载：

```text
../大作业1/STAEformer.py
../大作业1/STAEformer.yaml
../大作业1/data/PEMS08/data.npz
../大作业1/data/PEMS08/index.npz
../大作业1/results/baseline_PEMS08_checkpoint.pth
```

成功时返回未来 12 步、每步 5 分钟的预测流量。失败时返回 `available=false`，大模型只能解释失败原因，不能编造预测。

## 6. 当前边界

- 大作业1：已支持基于测试窗口的 STAEformer 真推理。
- 大作业2：当前是检测能力和训练结果摘要；如果要“用户上传图片 -> YOLO 实时检测 -> 大模型分析”，还需要再加图片上传接口和 YOLO 推理封装。
- Dify：源码由 `dify-1.14.2.zip` 提供，当前采用 Docker Compose 启动，TravelQA 作为外部 HTTP 工具服务接入。
