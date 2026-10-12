from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

import yaml
from ultralytics import YOLO



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run prediction with a trained YOLO model.")
    parser.add_argument("--config", required=True, help="Path to experiment yaml")
    parser.add_argument("--weights", required=True, help="Path to trained weights")
    parser.add_argument("--source", required=True, help="Image or directory to predict")
    parser.add_argument("--project", default="outputs/predict")
    parser.add_argument("--name", default="tt100k_predict")
    return parser.parse_args()



def load_config(path: str) -> Dict[str, Any]:
    config_path = Path(path).resolve()
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))



def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    model = YOLO(args.weights)
    predict_args = dict(config.get("predict", {}))
    predict_args.update({"source": args.source, "project": args.project, "name": args.name})
    model.predict(**predict_args)


if __name__ == "__main__":
    main()
