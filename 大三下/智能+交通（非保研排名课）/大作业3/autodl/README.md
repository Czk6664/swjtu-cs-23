# autodl

<!-- directory-guide:start -->
## 本层内容介绍

这里是“智能+交通”课程下的“autodl”目录，主要用于整理此模块的源码及配套文件。

**阅读建议：**从上级项目说明确认模块职责，再结合文件名查找实现；具体入口和运行方法以源码及原说明为准。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **8 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

- **代码与脚本（7 份）**：[download_model.sh](download_model.sh)、[login_swanlab.sh](login_swanlab.sh)等；完整列表见本页导航。
- **文档与说明（1 份）**：[requirements-autodl.txt](requirements-autodl.txt)。

<!-- directory-guide:end -->

所属课程：[智能+交通](../../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [download_model.sh](download_model.sh)
- [login_swanlab.sh](login_swanlab.sh)
- [preflight.py](preflight.py)
- [requirements-autodl.txt](requirements-autodl.txt)
- [retrain_v2.sh](retrain_v2.sh)
- [retrain_v4.sh](retrain_v4.sh)
- [run_ab_eval.sh](run_ab_eval.sh)
- [train_autodl.sh](train_autodl.sh)

[返回上级目录](../README.md)

## 原有项目说明

# AutoDL QLoRA Training Bundle

This bundle downloads `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` from the
ModelScope community and fine-tunes it with QLoRA.
The dataset is already included: 1104 training rows and 124 validation rows.

## 1. Upload and extract

```bash
tar -xzf autodl_travelqa_bundle_20260602.tar.gz
cd autodl_travelqa_bundle
```

Choose an AutoDL PyTorch CUDA image and a GPU with at least 24 GB VRAM.

## 2. Log in to SwanLab

Get an API key from <https://swanlab.cn/settings>, then run:

```bash
bash autodl/login_swanlab.sh
```

For a non-interactive login:

```bash
export SWANLAB_API_KEY='your-api-key'
bash autodl/login_swanlab.sh
```

Do not write an API key into any file in this bundle.

## 3. Download, train and evaluate

```bash
bash autodl/train_autodl.sh
```

The script installs Python dependencies, downloads the ModelScope model
snapshot with a resumable cache, verifies the CUDA GPU, dependencies, dataset
and downloaded weights, runs QLoRA training, uploads metrics to SwanLab, and
generates eight deterministic smoke-check responses after training.
At the end of training, the Trainer reloads the checkpoint with the lowest
validation loss before writing the adapter in the main output directory.

## Useful switches

```bash
SKIP_INSTALL=1 bash autodl/train_autodl.sh   # dependencies already installed
SKIP_DOWNLOAD=1 bash autodl/train_autodl.sh  # model snapshot already downloaded
SKIP_EVAL=1 bash autodl/train_autodl.sh      # train only
bash autodl/download_model.sh                # download only
```

For the v4 retraining patch on an existing AutoDL instance, reuse the already
downloaded ModelScope weights:

```bash
SKIP_INSTALL=1 bash autodl/retrain_v4.sh
```

The model is public, so ModelScope login is not required. For a private
ModelScope repository, log in before downloading:

```bash
export MODELSCOPE_API_TOKEN='your-modelscope-token'
modelscope login --token "${MODELSCOPE_API_TOKEN}"
```

## Outputs

```text
finetune/outputs/deepseek-travelqa-lora-v4/ # LoRA adapter and Trainer metrics
finetune/outputs/eval/smoke_results.jsonl # generated smoke-check responses
logs/                                    # terminal training logs
```

## 4. Run the 100-case A/B manual evaluation

After training, compare the untouched base model with the LoRA adapter:

```bash
bash autodl/run_ab_eval.sh
```

This is resumable. It writes progress after every generated answer. The full
comparison runs 100 questions against each model, so it takes longer than the
eight-case smoke check.

For a quick three-question pipeline check:

```bash
bash autodl/run_ab_eval.sh --limit 3 --output-dir outputs/ab_eval_quick
```

Download and open this file in a browser to review answers one by one:

```text
finetune/outputs/ab_eval/manual_review.html
```

Your ratings are saved in browser local storage. Click `导出人工评分 CSV` in
the HTML page when the manual review is complete.

This v4 recipe uses two epochs and writes the new adapter to
`deepseek-travelqa-lora-v4`, preserving the previous experiment directories.

