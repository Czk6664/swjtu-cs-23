from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

import yaml
from ultralytics import YOLO

from src.tt100k.metrics import save_metrics



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a YOLO model on TT100K.")
    parser.add_argument("--config", required=True, help="Path to experiment yaml")
    parser.add_argument("--weights", required=True, help="Path to trained weights")
    parser.add_argument("--output", default="outputs/report_assets/metrics/val_metrics.json")
    parser.add_argument("--device", default=None, help="Override device from config")
    return parser.parse_args()



def load_config(path: str) -> Dict[str, Any]:
    config_path = Path(path).resolve()
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))



def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    model = YOLO(args.weights)
    val_args = dict(config.get("val", {}))
    if args.device is not None:
        val_args["device"] = args.device
    results = model.val(**val_args)

    metrics = {
        "map50": float(results.box.map50),
        "map50_95": float(results.box.map),
        "precision": float(results.box.mp),
        "recall": float(results.box.mr),
    }
    save_metrics(metrics, Path(args.output).resolve())
    print(metrics)


if __name__ == "__main__":
    main()
