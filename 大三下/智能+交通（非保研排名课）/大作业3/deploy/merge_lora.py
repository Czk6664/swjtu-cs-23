r"""合并 LoRA 适配器到基座, 输出 BF16 完整模型 (Windows / CPU 即可).

合并后是 14.2 GB safetensors, 仍不能直接放 8GB 显存推理, 需再走 quantize_gguf.py 转 GGUF.

约定的目录结构 (相对路径默认基于此):
    workspace/
    ├── deploy/                          <- 本脚本所在目录
    │   ├── merge_lora.py
    │   └── ...
    ├── deepseek_lora__v4/              <- LoRA 适配器
    │   └── deepseek-travelqa-lora-v4/
    │       ├── adapter_model.safetensors
    │       └── adapter_config.json
    └── models/                         <- download_model.ps1 自动建
        ├── DeepSeek-R1-Distill-Qwen-7B/             (基座, 14.2 GB)
        └── DeepSeek-R1-Distill-Qwen-7B-merged/      (合并产物, 14.2 GB)

用法 (最简, 默认相对路径):
    cd deploy
    python merge_lora.py

显式覆盖 (任何路径都行):
    python merge_lora.py --base E:\hf\base --adapter E:\lora\v4 --out E:\hf\merged
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE   = SCRIPT_DIR.parent                    # deploy/ 的父目录
DEFAULT_BASE    = WORKSPACE / "models" / "DeepSeek-R1-Distill-Qwen-7B"
DEFAULT_ADAPTER = WORKSPACE / "deepseek_lora__v4" / "deepseek-travelqa-lora-v4"
DEFAULT_OUT     = WORKSPACE / "models" / "DeepSeek-R1-Distill-Qwen-7B-merged"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base",    default=str(DEFAULT_BASE),
                   help=f"基座模型目录 (HF 格式, 默认 {DEFAULT_BASE})")
    p.add_argument("--adapter", default=str(DEFAULT_ADAPTER),
                   help=f"LoRA 适配器目录 (含 adapter_model.safetensors, 默认 {DEFAULT_ADAPTER})")
    p.add_argument("--out",     default=str(DEFAULT_OUT),
                   help=f"合并后模型输出目录 (默认 {DEFAULT_OUT})")
    p.add_argument("--dtype",   default="bfloat16", choices=["bfloat16", "float16", "float32"])
    p.add_argument("--device",  default="cpu", choices=["cpu", "cuda"],
                   help="合并用设备; cpu 慢但稳, 8GB 显存不必勉强上 cuda")
    return p.parse_args()


def dir_size(p: Path) -> float:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1e9


def main() -> None:
    args = parse_args()
    base_path    = Path(args.base).resolve()
    adapter_path = Path(args.adapter).resolve()
    out_path     = Path(args.out).resolve()

    dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16, "float32": torch.float32}[args.dtype]

    print(f"[merge] 工作目录  : {SCRIPT_DIR}")
    print(f"[merge] 基座  : {base_path}")
    print(f"[merge] 适配器: {adapter_path}")
    print(f"[merge] 输出  : {out_path}  dtype={args.dtype} device={args.device}")

    if not (base_path / "config.json").exists():
        sys.exit(f"[merge] 找不到 {base_path}/config.json —— 请先跑 download_model.ps1 拉基座")
    if not (adapter_path / "adapter_model.safetensors").exists():
        sys.exit(f"[merge] 找不到 {adapter_path}/adapter_model.safetensors —— 请确认 LoRA 路径")

    print("[merge] 加载基座 (这步最慢, 约 1-2 分钟)...")
    base = AutoModelForCausalLM.from_pretrained(
        str(base_path),
        dtype=dtype,
        device_map=args.device,
        low_cpu_mem_usage=True,
    )
    print("[merge] 加载 LoRA 适配器...")
    model = PeftModel.from_pretrained(base, str(adapter_path))
    print("[merge] merge_and_unload() ...")
    model = model.merge_and_unload()

    out_path.mkdir(parents=True, exist_ok=True)
    print(f"[merge] 保存合并后模型到 {out_path} ...")
    model.save_pretrained(str(out_path), safe_serialization=True, max_shard_size="5GB")

    print("[merge] 复制 tokenizer (从基座)...")
    tok = AutoTokenizer.from_pretrained(str(base_path), trust_remote_code=True)
    tok.save_pretrained(str(out_path))

    copied = []
    for fname in ("generation_config.json", "special_tokens_map.json"):
        src = base_path / fname
        if src.exists() and not (out_path / fname).exists():
            shutil.copy2(src, out_path / fname)
            copied.append(fname)
    if copied:
        print(f"[merge] 补拷配置文件: {', '.join(copied)}")

    print(f"[merge] 完成. 合并后大小: {dir_size(out_path):.1f} GB")
    print(f"[merge] 下一步: python quantize_gguf.py  (默认也用相对路径)")


if __name__ == "__main__":
    main()
