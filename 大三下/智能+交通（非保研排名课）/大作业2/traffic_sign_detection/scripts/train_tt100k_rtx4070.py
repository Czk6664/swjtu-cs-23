from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

import yaml
from ultralytics import YOLO


PRESETS = {
    "safe": {
        "model": "yolo11n.pt",
        "imgsz": 640,
        "batch": 16,
        "workers": 4,
        "name": "yolo11n_tt100k_rtx4070_safe",
    },
    "balanced": {
        "model": "yolo11n.pt",
        "imgsz": 640,
        "batch": 32,
        "workers": 8,
        "name": "yolo11n_tt100k_rtx4070_balanced",
    },
    "aggressive": {
        "model": "yolo11s.pt",
        "imgsz": 640,
        "batch": 16,
        "workers": 8,
        "name": "yolo11s_tt100k_rtx4070_aggressive",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train TT100K on an RTX 4070 Laptop with preset profiles.")
    parser.add_argument(
        "--profile",
        choices=sorted(PRESETS),
        default="balanced",
        help="Preset for 8 GB laptop GPUs: safe, balanced, or aggressive.",
    )
    parser.add_argument(
        "--config",
        default="configs/experiments/yolo11n_tt100k_rtx4070.yaml",
        help="Base experiment yaml. Preset values are applied on top.",
    )
    parser.add_argument("--device", default="0", help="CUDA device id")
    parser.add_argument("--epochs", type=int, default=None, help="Override epoch count")
    parser.add_argument("--batch", type=int, default=None, help="Override batch size")
    parser.add_argument("--imgsz", type=int, default=None, help="Override image size")
    parser.add_argument("--workers", type=int, default=None, help="Override worker count")
    parser.add_argument("--name", default=None, help="Override run name")
    return parser.parse_args()


def load_config(path: str) -> Dict[str, Any]:
    config_path = Path(path).resolve()
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    preset = PRESETS[args.profile]

    config["model"] = preset["model"]
    train_args = dict(config.get("train", {}))
    train_args.update(
        {
            "imgsz": preset["imgsz"],
            "batch": preset["batch"],
            "workers": preset["workers"],
            "name": preset["name"],
            "device": args.device,
            "amp": True,
        }
    )

    if args.epochs is not None:
        train_args["epochs"] = args.epochs
    if args.batch is not None:
        train_args["batch"] = args.batch
    if args.imgsz is not None:
        train_args["imgsz"] = args.imgsz
    if args.workers is not None:
        train_args["workers"] = args.workers
    if args.name is not None:
        train_args["name"] = args.name

    model = YOLO(config["model"])
    model.train(**train_args)


if __name__ == "__main__":
    main()
