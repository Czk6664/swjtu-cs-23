# deploy

<!-- directory-guide:start -->
## 本层内容介绍

这里是“智能+交通”课程下的“deploy”目录，主要用于整理部署配置或集群资源定义。

**阅读建议：**先阅读上级部署说明并确认所需环境，再理解各配置的作用；不要把它们当作普通课件打开学习。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **4 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

- **配置及其他配套文件（1 份）**：[Modelfile](Modelfile)。
- **代码与脚本（2 份）**：[merge_lora.py](merge_lora.py)、[quantize_gguf.py](quantize_gguf.py)。
- **文档与说明（1 份）**：[requirements-deploy.txt](requirements-deploy.txt)。

<!-- directory-guide:end -->

所属课程：[智能+交通](../../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [merge_lora.py](merge_lora.py)
- [Modelfile](Modelfile)
- [quantize_gguf.py](quantize_gguf.py)
- [requirements-deploy.txt](requirements-deploy.txt)

[返回上级目录](../README.md)

## 原有项目说明

# 成都交通 Q&A LoRA —— Windows 部署包 (基座已下好)

## 一句话: 把 `deploy\` + `deepseek_lora__v4\` 平级放好, 在 `deploy\` 里跑 2 条命令

## 约定的目录结构 (相对路径默认基于此)

```
workspace\                              <- 你建的根目录, 任意位置都行
├── deploy\                             <- 本目录
│   ├── README.md
│   ├── merge_lora.py                   # ① 合并 LoRA
│   ├── quantize_gguf.py                # ② 量化 GGUF Q4_K_M
│   ├── Modelfile                       # ③ Ollama 配方
│   └── requirements-deploy.txt
├── deepseek_lora__v4\                  <- LoRA 适配器 (从 AutoDL 下载)
│   └── deepseek-travelqa-lora-v4\
│       ├── adapter_model.safetensors
│       └── adapter_config.json
└── models\                             <- ★ 基座已下好
    └── DeepSeek-R1-Distill-Qwen-7B\             (基座 14.2 GB, 跑完可删)
```

合并 + 量化后会新建：

```
└── models\
    ├── DeepSeek-R1-Distill-Qwen-7B-merged\      (合并 14.2 GB, 跑完可删)
    ├── travelqa-q4km_work\                      (F16 GGUF + llama-quantize.exe 缓存, 可删)
    └── travelqa-q4km.gguf                       (★ 最终 4.7 GB, 保留)
```

## 目标机器准备 (RTX 4070 8GB / 任何 Windows)

```powershell
# 1. Python 3.10+
winget install --id Python.Python.3.12 -e --source winget

# 2. 装 Ollama
winget install --id Ollama.Ollama -e --source winget
# 或官网: https://ollama.com/download

# 3. 装 Python 依赖 (在 deploy\ 目录下)
cd deploy
pip install -r requirements-deploy.txt
```

## 3 步部署 (在 deploy\ 目录下, 全程默认相对路径)

```powershell
cd deploy

# ① 合并 LoRA → 合并模型 (14.2 GB, ~2-3 min on CPU)
python merge_lora.py

# ② 量化 → Q4_K_M GGUF (4.7 GB, ~3-5 min)
python quantize_gguf.py

# ③ 拷 Modelfile + ollama create
copy Modelfile ..\models\
ollama create travelqa -f ..\models\Modelfile
ollama serve
# 监听 http://localhost:11434/v1
```

**全部命令** 不带任何参数。默认相对路径自动找 `..\models\DeepSeek-R1-Distill-Qwen-7B\` (基座) 和 `..\deepseek_lora__v4\` (LoRA)。

## 基座路径不是默认位置? 一步覆盖

```powershell
# 比如基座在 E:\hf\base
python merge_lora.py --base E:\hf\base

# 或者手动建立软链让默认路径生效
mklink /D "..\models\DeepSeek-R1-Distill-Qwen-7B" "E:\hf\base"
```

## 测试

```powershell
# 命令行
ollama run travelqa "成都今天限行吗"

# 集成到 TravelQAApp (改 config.yaml)
llm:
  provider: openai_compatible
  base_url: http://localhost:11434/v1
  model: travelqa

python scripts\chat.py --demo
python eval\run_eval.py
```

## 故障排查

| 现象 | 排查 |
|---|---|
| 找不到 `..\models\DeepSeek-R1-Distill-Qwen-7B\config.json` | 用 `--base` 指定实际基座位置 |
| 找不到 `..\deepseek_lora__v4\...\adapter_model.safetensors` | 用 `--adapter` 指定 LoRA 位置 |
| `pip install gguf` 失败 | 升级 pip: `python -m pip install -U pip` |
| 合并 OOM | 默认 `device=cpu` (8GB 显存跑合并会爆) |
| `llama-quantize.exe` 未找到 | 删 `travelqa-q4km_work\` 重跑, 会自动重下 |
| Ollama 报 `model not found` | `ollama list` 确认; `ollama rm travelqa && ollama create ...` |
| 回答循环/重复 | Modelfile 已设 `repeat_penalty 1.1` |
| 推理慢 | 启动 ollama 时设 `OLLAMA_NUM_GPU=28` (8GB 显存 7B Q4 约 28 层) |

## 产物大小

| 产物 | 大小 | 保留? |
|---|---|---|
| 基座 safetensors | 14.2 GB | 可删 (合并后) |
| 合并后 BF16 | 14.2 GB | 可删 (量化后) |
| F16 GGUF (`travelqa-q4km_work\f16.gguf`) | 14.2 GB | 可删 (量化后) |
| **Q4_K_M GGUF** | **4.7 GB** | **★ 保留** |
| Ollama 加载后 | +4.7 GB | 在 `C:\Users\<you>\.ollama\models\` |
| **总磁盘占用** | **~5 GB** | 仅 Q4_K_M + Ollama 缓存 |

