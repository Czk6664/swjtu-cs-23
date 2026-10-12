"""Download the configured ModelScope base model with resumable caching."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

DEFAULT_MODEL_ID = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
DEFAULT_LOCAL_DIR = "models/DeepSeek-R1-Distill-Qwen-7B"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-id",
        default=os.getenv("MODELSCOPE_MODEL_ID", DEFAULT_MODEL_ID),
    )
    parser.add_argument("--revision", default=os.getenv("MODELSCOPE_MODEL_REVISION", ""))
    parser.add_argument("--local-dir", default=os.getenv("MODEL_DIR", DEFAULT_LOCAL_DIR))
    args = parser.parse_args()

    try:
        from modelscope import snapshot_download
    except ModuleNotFoundError:
        raise SystemExit(
            "[download] modelscope is missing. "
            "Run: python -m pip install -r autodl/requirements-autodl.txt"
        )

    local_dir = Path(args.local_dir).expanduser().resolve()
    local_dir.mkdir(parents=True, exist_ok=True)
    revision = args.revision or None
    print(f"[download] ModelScope model: {args.model_id}")
    if revision:
        print(f"[download] revision: {revision}")
    print(f"[download] dir : {local_dir}")
    kwargs = {"model_id": args.model_id, "local_dir": str(local_dir)}
    if revision:
        kwargs["revision"] = revision
    downloaded = snapshot_download(**kwargs)
    print(f"[download] complete: {Path(downloaded).resolve()}")


if __name__ == "__main__":
    main()
