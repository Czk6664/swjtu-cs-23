"""手动触发一轮飞轮重训（门控晋升/保留）。

用法:
    python scripts/trigger_retrain.py --model detection
    python scripts/trigger_retrain.py --model forecast --inject-regression
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from capstone.pipeline import TrafficDecisionSystem, to_json  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="detection", choices=["detection", "forecast"])
    ap.add_argument("--inject-regression", action="store_true",
                    help="注入劣化候选以演示门控拦截")
    args = ap.parse_args()

    sys_ = TrafficDecisionSystem()
    report = sys_.flywheel_round(args.model, inject_regression=args.inject_regression)
    print(to_json(report))


if __name__ == "__main__":
    main()
