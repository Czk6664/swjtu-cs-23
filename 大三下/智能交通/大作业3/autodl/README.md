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
