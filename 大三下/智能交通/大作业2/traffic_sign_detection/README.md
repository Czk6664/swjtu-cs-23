# TT100K Object Detection Framework

This directory contains a practical TT100K traffic-sign detection experiment framework built around Ultralytics YOLO.

## Scope

- TT100K annotation conversion and split generation
- YOLO dataset config and experiment configs
- Training, validation, and prediction entrypoints
- Metric aggregation and report-asset export for the LaTeX course report

## Quick start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Prepare TT100K in YOLO format:

```bash
python scripts/prepare_tt100k.py --src "PATH/TO/TT100K" --dest data/tt100k_yolo
```

3. Train a baseline model:

```bash
python train.py --config configs/experiments/yolo11n_tt100k.yaml
```

4. Validate a checkpoint:

```bash
python val.py --config configs/experiments/yolo11n_tt100k.yaml --weights runs/tt100k/yolo11n_tt100k/weights/best.pt
```

5. Run prediction:

```bash
python predict.py --config configs/experiments/yolo11n_tt100k.yaml --weights runs/tt100k/yolo11n_tt100k/weights/best.pt --source data/tt100k_yolo/images/test
```
