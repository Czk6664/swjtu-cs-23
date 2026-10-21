# traffic_sign_detection

所属课程：[智能+交通](../../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [configs/](configs/README.md)
- [demo/](demo/README.md)
- [docs/](docs/README.md)
- [experiments/](experiments/README.md)
- [models/](models/README.md)
- [outputs/](outputs/README.md)
- [runs/](runs/README.md)
- [scripts/](scripts/README.md)
- [src/](src/README.md)
- [.gitkeep](.gitkeep)
- [export_report_assets.py](export_report_assets.py)
- [predict.py](predict.py)
- [README_4070_AUTOTUNE.md](README_4070_AUTOTUNE.md)
- [requirements.txt](requirements.txt)
- [run_experiments.bat](run_experiments.bat)
- [train.py](train.py)
- [val.py](val.py)
- [yolo11n.pt](yolo11n.pt)

[返回上级目录](../README.md)

## 原有项目说明

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

