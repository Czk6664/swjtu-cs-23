#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export MODELSCOPE_CACHE="${MODELSCOPE_CACHE:-${ROOT_DIR}/.cache/modelscope}"
export MODEL_DIR="${MODEL_DIR:-${ROOT_DIR}/models/DeepSeek-R1-Distill-Qwen-7B}"
export TRAVELQA_BASE_MODEL="${MODEL_DIR}"

python autodl/preflight.py --after-download
python finetune/ab_eval.py "$@"

echo "A/B evaluation complete."
echo "CSV : finetune/outputs/ab_eval/ab_results.csv"
echo "HTML: finetune/outputs/ab_eval/manual_review.html"
