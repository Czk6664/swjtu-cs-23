"""
Gold-YOLO GD (Gather-and-Distribute) Inspired Improvement
Paper: NeurIPS 2023, arXiv:2309.12314

Simplified implementation using Ultralytics A2C2f blocks (which implement
area-attention, a concept related to Gold-YOLO's gather-distribute mechanism)
combined with C2PSA at P3/P4 levels for enhanced multi-scale feature aggregation.

Key changes vs baseline YOLO11n:
  - A2C2f replaces C3k2 at P4/P5 (gather-distribute style attention)
  - C2PSA added at P3 level (position-sensitive attention on high-res features)
  - SCDown replaces Conv stride-2 (information-preserving downsampling)

Usage:
    cd traffic_sign_detection
    python experiments/gold_yolo_gd/train_gold_yolo_gd.py --epochs 50 --batch 16
"""

import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # traffic_sign_detection/
sys.path.insert(0, str(ROOT))


def create_model_yaml(output_path: Path):
    """Create a Gold-YOLO inspired model YAML with A2C2f + C2PSA + SCDown."""
    yaml_content = """\
# Gold-YOLO GD Inspired YOLO11n
# Changes: A2C2f at P4/P5, C2PSA at P3, SCDown for downsampling

nc: 12
scales:
  n: [0.50, 0.25, 1024]

backbone:
  - [-1, 1, Conv, [64, 3, 2]]          # 0-P1/2
  - [-1, 1, SCDown, [128, 3, 2]]        # 1-P2/4 (SCDown from YOLOv10)
  - [-1, 2, C3k2, [256, False, 0.25]]   # 2
  - [-1, 1, Conv, [256, 3, 2]]          # 3-P3/8
  - [-1, 2, C3k2, [512, False, 0.25]]   # 4
  - [-1, 1, SCDown, [512, 3, 2]]        # 5-P4/16 (SCDown)
  - [-1, 2, A2C2f, [512, 2, True, 1, 2.0]]  # 6 (A2C2f from YOLO11)
  - [-1, 1, SCDown, [1024, 3, 2]]       # 7-P5/32 (SCDown)
  - [-1, 2, A2C2f, [1024, 2, True, 1, 2.0]] # 8 (A2C2f)
  - [-1, 1, SPPF, [1024, 5]]            # 9
  - [-1, 2, C2PSA, [1024]]              # 10

head:
  - [-1, 1, nn.Upsample, [None, 2, "nearest"]]
  - [[-1, 6], 1, Concat, [1]]
  - [-1, 2, C3k2, [512, False]]         # 13

  - [-1, 1, nn.Upsample, [None, 2, "nearest"]]
  - [[-1, 4], 1, Concat, [1]]
  - [-1, 2, C3k2, [512, False]]         # 16 (P3) - larger channels for C2PSA
  - [-1, 1, C2PSA, [512]]               # 17: C2PSA at P3 (Gold-YOLO style)

  - [-1, 1, Conv, [512, 3, 2]]          # P3 down
  - [[-1, 13], 1, Concat, [1]]
  - [-1, 2, A2C2f, [512, 2, True, 1, 2.0]]  # 20 (P4)

  - [-1, 1, Conv, [512, 3, 2]]          # P4 down
  - [[-1, 10], 1, Concat, [1]]
  - [-1, 2, A2C2f, [1024, 2, True, 1, 2.0]] # 23 (P5)

  - [[17, 20, 23], 1, Detect, [nc]]
"""
    output_path.write_text(yaml_content, encoding="utf-8")
    print(f"[Gold-YOLO GD] Model YAML: {output_path}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--imgsz", type=int, default=704)
    p.add_argument("--device", default="0")
    p.add_argument("--data", default=str(ROOT / "configs" / "dataset" / "tt100k.yaml"))
    p.add_argument("--name", default="yolo11n_gold_yolo_gd_704_e50")
    return p.parse_args()


def main():
    args = parse_args()

    # Generate model YAML
    yaml_path = ROOT / "experiments" / "gold_yolo_gd" / "yolo11n_gold_yolo_gd.yaml"
    create_model_yaml(yaml_path)

    # Verify model loads
    from ultralytics import YOLO
    print(f"[Gold-YOLO GD] Loading model: {yaml_path}")
    model = YOLO(str(yaml_path))
    params = sum(p.numel() for p in model.model.parameters())
    print(f"[Gold-YOLO GD] Parameters: {params:,}")

    # Train
    model.train(
        data=args.data, epochs=args.epochs, imgsz=args.imgsz,
        batch=args.batch, device=args.device, workers=4,
        project=str(ROOT / "runs" / "tt100k"), name=args.name,
        pretrained=False, optimizer="auto", lr0=0.01, lrf=0.01,
        momentum=0.937, weight_decay=0.0005, warmup_epochs=3.0,
        close_mosaic=10, mixup=0.15, cos_lr=True, multi_scale=0.2,
    )
    print(f"\n[DONE] Results in runs/tt100k/{args.name}")


if __name__ == "__main__":
    main()
