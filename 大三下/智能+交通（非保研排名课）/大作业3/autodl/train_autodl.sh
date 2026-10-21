#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export MODELSCOPE_CACHE="${MODELSCOPE_CACHE:-${ROOT_DIR}/.cache/modelscope}"
export MODEL_DIR="${MODEL_DIR:-${ROOT_DIR}/models/DeepSeek-R1-Distill-Qwen-7B}"
export TRAVELQA_BASE_MODEL="${MODEL_DIR}"
export SWANLAB_PROJ_NAME="${SWANLAB_PROJ_NAME:-chengdu-travelqa-qlora}"
export SWANLAB_EXP_NAME="${SWANLAB_EXP_NAME:-deepseek-r1-qwen7b-$(date +%Y%m%d-%H%M%S)}"
export SWANLAB_TAGS="${SWANLAB_TAGS:-autodl,qlora,travelqa}"

mkdir -p logs
LOG_FILE="logs/train_$(date +%Y%m%d_%H%M%S).log"

if [[ "${SKIP_INSTALL:-0}" != "1" ]]; then
  python -m pip install --upgrade pip
  python -m pip install -r autodl/requirements-autodl.txt
fi

python autodl/preflight.py

if [[ "${SKIP_DOWNLOAD:-0}" != "1" ]]; then
  bash autodl/download_model.sh
fi

python autodl/preflight.py --after-download

echo "Starting QLoRA training. SwanLab project: ${SWANLAB_PROJ_NAME}"
python finetune/train_lora.py \
  --run \
  --base-model "${MODEL_DIR}" \
  --run-name "${SWANLAB_EXP_NAME}" \
  2>&1 | tee "${LOG_FILE}"

if [[ "${SKIP_EVAL:-0}" != "1" ]]; then
  python finetune/eval_adapter.py \
    --base-model "${MODEL_DIR}" \
    --adapter-dir outputs/deepseek-travelqa-lora-v4
fi

echo "Done. Adapter: finetune/outputs/deepseek-travelqa-lora-v4"
echo "Log file: ${LOG_FILE}"
