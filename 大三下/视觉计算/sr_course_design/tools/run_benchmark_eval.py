"""Run benchmark-compatible SR inference and evaluation.

The benchmark directory must follow the same paired layout used elsewhere:

<benchmark_root>/
├── LR/
└── HR/

This helper does not download datasets. It makes Set5/Set14/BSD100/Urban100
runs reproducible when those datasets are prepared locally.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.eval import evaluate_directory
from src.infer import run_inference


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark-compatible SR inference/evaluation helper")
    parser.add_argument("--benchmark-root", required=True, type=str)
    parser.add_argument("--name", required=True, type=str, help="Benchmark name, e.g. Set5 or Urban100")
    parser.add_argument("--model", required=True, choices=["bicubic", "srcnn", "imdn", "ca_imdn", "idb_imdn"])
    parser.add_argument("--scale", default=2, type=int)
    parser.add_argument("--num-features", default=32, type=int)
    parser.add_argument("--num-blocks", default=4, type=int)
    parser.add_argument("--checkpoint", default="", type=str)
    parser.add_argument("--output-root", default="./results/benchmarks", type=str)
    parser.add_argument("--rgb", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    benchmark_root = Path(args.benchmark_root)
    lr_dir = benchmark_root / "LR"
    hr_dir = benchmark_root / "HR"
    if not lr_dir.exists() or not hr_dir.exists():
        raise FileNotFoundError(f"Expected LR/HR directories under {benchmark_root}")

    run_name = f"{args.name}_{args.model}_x{args.scale}"
    output_dir = Path(args.output_root) / run_name
    csv_path = Path(args.output_root) / f"{run_name}_metrics.csv"

    run_inference(
        model_name=args.model,
        scale=args.scale,
        input_path=str(lr_dir),
        output_path=str(output_dir),
        num_features=args.num_features,
        checkpoint_path=args.checkpoint or None,
        num_blocks=args.num_blocks,
    )
    evaluate_directory(
        result_dir=output_dir,
        target_dir=hr_dir,
        scale=args.scale,
        use_y_channel=not args.rgb,
        csv_path=csv_path,
    )


if __name__ == "__main__":
    main()
