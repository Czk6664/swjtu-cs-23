from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

import yaml
from ultralytics import YOLO

from models import patch_ultralytics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a YOLO model on TT100K.")
    parser.add_argument("--config", required=True, help="Path to experiment yaml")
    parser.add_argument("--device", default=None, help="Override device from config")
    parser.add_argument("--batch", type=int, default=None, help="Override batch size")
    parser.add_argument("--epochs", type=int, default=None, help="Override epoch count")
    parser.add_argument("--imgsz", type=int, default=None, help="Override image size")
    parser.add_argument("--workers", type=int, default=None, help="Override dataloader workers")
    parser.add_argument("--name", default=None, help="Override run name")
    return parser.parse_args()



def load_config(path: str) -> Dict[str, Any]:
    config_path = Path(path).resolve()
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))



def main() -> None:
    patch_ultralytics()
    args = parse_args()
    config = load_config(args.config)
    model = YOLO(config["model"])
    train_args = dict(config.get("train", {}))
    if args.device is not None:
        train_args["device"] = args.device
    if args.batch is not None:
        train_args["batch"] = args.batch
    if args.epochs is not None:
        train_args["epochs"] = args.epochs
    if args.imgsz is not None:
        train_args["imgsz"] = args.imgsz
    if args.workers is not None:
        train_args["workers"] = args.workers
    if args.name is not None:
        train_args["name"] = args.name
    model.train(**train_args)


if __name__ == "__main__":
    main()
