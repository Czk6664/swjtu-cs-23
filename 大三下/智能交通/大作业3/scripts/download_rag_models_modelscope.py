"""Download semantic RAG models from ModelScope into project-local directories."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = (
    ("Xorbits/bge-m3", ROOT / "models" / "rag" / "bge-m3"),
    ("AI-ModelScope/bge-reranker-v2-m3", ROOT / "models" / "rag" / "bge-reranker-v2-m3"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def complete(path: Path) -> bool:
    return (path / "config.json").exists() and any(path.glob("*.safetensors"))


def main() -> None:
    args = parse_args()
    try:
        from modelscope import snapshot_download
    except ModuleNotFoundError:
        raise SystemExit("ModelScope is missing: python -m pip install modelscope")

    for model_id, local_dir in MODELS:
        if complete(local_dir) and not args.force:
            print(f"[modelscope] reuse: {local_dir}")
            continue
        if local_dir.exists():
            print(f"[modelscope] removing incomplete snapshot: {local_dir}")
            shutil.rmtree(local_dir)
        local_dir.mkdir(parents=True, exist_ok=True)
        print(f"[modelscope] downloading {model_id} -> {local_dir}")
        snapshot_download(
            model_id=model_id,
            local_dir=str(local_dir),
            ignore_patterns=[
                "*.bin", "*.onnx", "*.ot", "*.h5", "*.msgpack",
                "onnx/*", "onnx/**", "openvino/*", "openvino/**",
            ],
        )
        if not complete(local_dir):
            raise SystemExit(f"[modelscope] incomplete safetensors snapshot: {local_dir}")
    print("[modelscope] semantic RAG models are ready")


if __name__ == "__main__":
    sys.exit(main())
