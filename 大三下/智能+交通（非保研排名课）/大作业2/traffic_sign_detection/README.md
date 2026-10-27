# traffic_sign_detection

<!-- directory-guide:start -->
## 本层内容介绍

这里是“智能+交通”课程下的“traffic_sign_detection”目录，主要用于整理包含依赖或构建配置的项目目录。

**阅读建议：**先读下方原有项目说明，了解功能和环境，再查看依赖文件与源代码。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **122 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

| 子目录 | 内容与用途 |
| --- | --- |
| [configs](configs/README.md) | 运行或实验配置文件 |
| [demo](demo/README.md) | 此模块的源码及配套文件 |
| [docs](docs/README.md) | 项目说明或参考文档 |
| [experiments](experiments/README.md) | 实验运行记录或分组结果 |
| [models](models/README.md) | 模型结构、损失函数或模型相关文件 |
| [outputs](outputs/README.md) | 实验或程序产生的结果文件 |
| [runs](runs/README.md) | 实验运行记录或分组结果 |
| [scripts](scripts/README.md) | 处理数据、生成材料或辅助运行的脚本工具 |
| [src](src/README.md) | 程序源代码与实现文件 |

- **配置及其他配套文件（1 份）**：[.gitkeep](.gitkeep)。
- **文档与说明（2 份）**：[README_4070_AUTOTUNE.md](README_4070_AUTOTUNE.md)、[requirements.txt](requirements.txt)。
- **代码与脚本（5 份）**：[export_report_assets.py](export_report_assets.py)、[predict.py](predict.py)等；完整列表见本页导航。
- **模型与序列化文件（1 份）**：[yolo11n.pt](yolo11n.pt)。

<!-- directory-guide:end -->

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

