#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

MODEL_DIR="${MODEL_DIR:-${ROOT_DIR}/models/DeepSeek-R1-Distill-Qwen-7B}"
ARGS=(
  --model-id "${MODELSCOPE_MODEL_ID:-deepseek-ai/DeepSeek-R1-Distill-Qwen-7B}"
  --local-dir "${MODEL_DIR}"
)
if [[ -n "${MODELSCOPE_MODEL_REVISION:-}" ]]; then
  ARGS+=(--revision "${MODELSCOPE_MODEL_REVISION}")
fi
python finetune/download_model.py "${ARGS[@]}"
