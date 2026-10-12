"""Fail fast on common AutoDL deployment mistakes before QLoRA training."""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_ROWS = {"train.jsonl": 1104, "val.jsonl": 124}
MIN_VRAM_GIB = 22.0


def require_module(name: str) -> object:
    try:
        return importlib.import_module(name)
    except Exception as exc:
        raise SystemExit(f"[preflight] cannot import {name}: {exc}") from exc


def check_python() -> None:
    if sys.version_info < (3, 9):
        raise SystemExit("[preflight] Python 3.9 or newer is required.")
    print(f"[preflight] Python: {sys.version.split()[0]}")


def check_dependencies() -> None:
    versions = {}
    for name in (
        "torch",
        "transformers",
        "peft",
        "datasets",
        "accelerate",
        "bitsandbytes",
        "modelscope",
        "swanlab",
        "yaml",
    ):
        module = require_module(name)
        versions[name] = getattr(module, "__version__", "installed")
    print("[preflight] dependencies:", json.dumps(versions, ensure_ascii=False))


def check_cuda() -> None:
    torch = require_module("torch")
    if not torch.cuda.is_available():
        raise SystemExit("[preflight] CUDA GPU was not detected. Select an AutoDL GPU instance.")
    props = torch.cuda.get_device_properties(0)
    vram_gib = props.total_memory / 1024**3
    print(f"[preflight] GPU: {props.name}, VRAM: {vram_gib:.1f} GiB, CUDA: {torch.version.cuda}")
    if vram_gib < MIN_VRAM_GIB:
        raise SystemExit(
            f"[preflight] at least {MIN_VRAM_GIB:.0f} GiB VRAM is required for this "
            "7B batch-size-2 recipe. Select a 24 GB or larger GPU."
        )


def check_dataset() -> None:
    data_dir = ROOT / "finetune" / "data"
    for filename, expected in EXPECTED_ROWS.items():
        path = data_dir / filename
        if not path.exists():
            raise SystemExit(f"[preflight] dataset file is missing: {path}")
        count = 0
        with path.open(encoding="utf-8") as file:
            for line_no, line in enumerate(file, start=1):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"[preflight] invalid JSONL: {path}:{line_no}: {exc}") from exc
                if not row.get("instruction") or not row.get("output"):
                    raise SystemExit(f"[preflight] blank instruction/output: {path}:{line_no}")
                count += 1
        if count != expected:
            raise SystemExit(f"[preflight] {path} has {count} rows; expected {expected}.")
        print(f"[preflight] dataset: {filename} = {count} rows")


def check_model() -> None:
    model_dir = Path(
        os.getenv("MODEL_DIR", str(ROOT / "models" / "DeepSeek-R1-Distill-Qwen-7B"))
    ).expanduser().resolve()
    required = ("config.json", "tokenizer_config.json")
    missing = [filename for filename in required if not (model_dir / filename).exists()]
    weights = list(model_dir.glob("*.safetensors"))
    if missing or not weights:
        details = f"missing={missing}, safetensors={len(weights)}"
        raise SystemExit(f"[preflight] incomplete model snapshot at {model_dir}: {details}")
    print(f"[preflight] model: {model_dir}")
    print(f"[preflight] safetensors files: {len(weights)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--after-download", action="store_true")
    args = parser.parse_args()
    check_python()
    check_dependencies()
    check_cuda()
    check_dataset()
    if args.after_download:
        check_model()
    print("[preflight] OK")


if __name__ == "__main__":
    main()
