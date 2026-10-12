#!/usr/bin/env bash
set -euo pipefail

if ! command -v swanlab >/dev/null 2>&1; then
  python -m pip install --upgrade swanlab
fi

if [[ -n "${SWANLAB_API_KEY:-}" ]]; then
  swanlab login --api-key "${SWANLAB_API_KEY}"
else
  echo "Paste the API key from https://swanlab.cn/settings when prompted."
  swanlab login
fi

echo "SwanLab login complete."
