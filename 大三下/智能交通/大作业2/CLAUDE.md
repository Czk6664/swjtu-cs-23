# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository scope

This repository currently contains a LaTeX course-report template rather than an implemented detection/training codebase. The working content is under `课程设计模版_2026年/`, centered on `main_report.tex` and the custom class file `report.cls`.

The user goal for this repository is to complete a course-design deliverable around recent traffic-sign detection research, TT100K-based experiments, and a final report formatted with this template. A Python-based YOLO experiment framework now exists under `traffic_sign_detection/`, while the LaTeX report remains under `课程设计模版_2026年/`.

When working in this repository, treat it as a two-surface project: experiment code in `traffic_sign_detection/` and report authoring in `课程设计模版_2026年/`.

## Common commands

Run report commands from `课程设计模版_2026年/`. Run experiment commands from `traffic_sign_detection/`.

### Build the PDF

Primary build flow observed from generated artifacts:

```bash
xelatex main_report.tex
bibtex main_report
xelatex main_report.tex
xelatex main_report.tex
```

This produces `main_report.pdf`.

### Fast rebuild when bibliography did not change

```bash
xelatex main_report.tex
```

### Clean generated artifacts manually

Delete intermediate files such as:

- `*.aux`
- `*.log`
- `*.out`
- `*.toc`
- `*.bbl`
- `*.blg`
- `*.bcf`
- `*.run.xml`
- `.texpadtmp/`

There is no project-local clean script yet.

### Set up the detection framework

```bash
pip install -r requirements.txt
```

Run this from `traffic_sign_detection/`.

### Prepare TT100K in YOLO format

```bash
python scripts/prepare_tt100k.py --src "PATH/TO/TT100K" --dest data/tt100k_yolo
```

This converts selected TT100K classes into YOLO labels and writes dataset config to `configs/dataset/tt100k.yaml`.

### Train a baseline detector

```bash
python train.py --config configs/experiments/yolo11n_tt100k.yaml
```

### Validate a trained checkpoint

```bash
python val.py --config configs/experiments/yolo11n_tt100k.yaml --weights runs/tt100k/yolo11n_tt100k/weights/best.pt
```

### Run prediction on images

```bash
python predict.py --config configs/experiments/yolo11n_tt100k.yaml --weights runs/tt100k/yolo11n_tt100k/weights/best.pt --source data/tt100k_yolo/images/test
```

### Export report assets

```bash
python scripts/collect_metrics.py --results-dir runs/tt100k/yolo11n_tt100k
python export_report_assets.py --from-dir outputs/report_assets --to-dir outputs/report_assets/final
```

### Quick script-level validation

```bash
python train.py --help
python val.py --help
python predict.py --help
python scripts/prepare_tt100k.py --help
```

There is no formal test suite yet.

### Single-test equivalent

There is no per-test command because the repository does not yet include pytest-based tests. The closest lightweight validation is running a single script with `--help` or a small local dry run.

## Tooling and environment assumptions

- The template is intended for **XeLaTeX**, not `pdflatex`; `report.cls` hard-requires XeTeX.
- The log shows successful compilation with **TeX Live 2025** on Windows.
- Chinese support comes from `ctex` and `xeCJK`.
- Bibliography is currently handled with **BibTeX** via `plain.bst` and `mybib.bib`.
- Graphics are resolved from directories declared in `report.cls`, especially `figures/`.

## High-level structure

### `traffic_sign_detection/`

This is the experiment code area for TT100K traffic-sign detection. It currently contains:

- YOLO-based train/validate/predict entrypoints
- TT100K annotation conversion and split scripts
- experiment YAML configs
- report-asset export helpers

Keep code and report concerns separated: training code belongs here, final narrative and formatted figures belong in `课程设计模版_2026年/`.

### `课程设计模版_2026年/main_report.tex`

This is the main report entrypoint. It contains:

- front-matter metadata (`\title`, `\stunum`, `\stuname`, etc.)
- report body structure
- section ordering for the final deliverable
- bibliography hookup via `mybib.bib`

At the moment it is still a sample report about image super-resolution, so any future work for this repository will likely replace most section content while keeping the template structure and metadata macros.

### `课程设计模版_2026年/report.cls`

This is the key formatting layer. Despite being named `report.cls`, it declares class `hfutreport` and loads `article` underneath. It defines:

- mandatory XeLaTeX/Chinese typesetting setup
- page geometry and line spacing
- cover-page metadata macros used by `main_report.tex`
- caption, TOC, bibliography, and hyperlink styling
- graphics search paths and listing/table formatting

When formatting behavior changes, check this file before editing the TeX body.

### `traffic_sign_detection/configs/`

This directory separates dataset config from experiment config:

- `configs/dataset/tt100k.yaml` describes the prepared YOLO dataset layout and class names
- `configs/experiments/*.yaml` controls model scale and train/val/predict defaults

Prefer changing experiments via YAML rather than hardcoding values in Python entry scripts.

### `traffic_sign_detection/src/tt100k/`

This package holds TT100K-specific logic:

- `classes.py` defines the selected 12-class mapping used for the course project
- `convert.py` converts TT100K bounding boxes into YOLO label lines
- `metrics.py` stores validation metrics for later reporting
- `visualize.py` contains simple bounding-box rendering helpers

### `traffic_sign_detection/scripts/`

This directory contains dataset and reporting utilities:

- `prepare_tt100k.py` converts TT100K into YOLO train/val/test layout
- `split_tt100k.py` recreates the split using the same conversion pipeline
- `collect_metrics.py` normalizes validation outputs into report-friendly CSV/JSON files

### `课程设计模版_2026年/mybib.bib`

Central bibliography database. The current file mixes references from unrelated topics plus a few super-resolution papers. If the repository shifts to TT100K traffic-sign detection, this file should be curated rather than appended blindly.

TT100K, YOLO, and related traffic-sign detection papers should be added deliberately rather than mixed into the existing sample bibliography.

### `课程设计模版_2026年/figures/`

Image assets used by the template cover and report figures.

## Current architectural reality

The repository now has two parallel work areas:

1. **Report-authoring tasks**
   - editing `课程设计模版_2026年/main_report.tex`
   - maintaining references in `课程设计模版_2026年/mybib.bib`
   - adding figures/tables that match the template

2. **Detection experiment tasks**
   - preparing TT100K into YOLO format
   - training / validating / predicting with Ultralytics YOLO
   - collecting metrics and exporting report assets

The experiment framework is present, but it is still a starter scaffold:
- no committed dataset
- no committed trained weights
- no formal pytest suite yet
- no custom model modification beyond YOLO baseline configs

Future Claude instances should verify whether the user wants baseline completion, model improvement, or report integration before editing files.

The current selected class subset is a 12-class TT100K mapping defined in `traffic_sign_detection/src/tt100k/classes.py`.

## Important template-specific details

- `main_report.tex` uses `\documentclass[bwprint]{report}`; this maps to the local `report.cls` file.
- The class expects title-page metadata macros such as `\stunum`, `\stuname`, `\stuclass`, `\supervisor`, and `\dateinput`.
- Bibliography is inserted with:

```tex
\bibliographystyle{plain}
\bibliography{mybib}
```

- The class sets `\graphicspath` to include `figures/`, `figure/`, `images/`, etc., so figure paths can usually stay relative to those folders.
- Build logs show some Windows font-resolution warnings, but PDF generation still completed.

## What future Claude instances should verify before acting

If the user asks for implementation work beyond the LaTeX report, first check whether new source directories have been added. In particular, verify whether the repo has gained files such as:

- `requirements.txt`, `environment.yml`, `pyproject.toml`
- `train.py`, `test.py`, `infer.py`
- `configs/`, `datasets/`, `models/`, `scripts/`
- TT100K label conversion or preprocessing scripts

Only after that should you document build/test/run commands for the ML part.

## Suggested direction implied by the user task

The assignment target is to study recent traffic-object/traffic-sign detection methods, train and test on TT100K with more than 10 classes, perform multi-object recognition in traffic scenes, analyze failure cases, propose improvements, and finish the report in this template. Since the repository does not yet contain that implementation, future work will likely involve creating a parallel experiment code area and then updating `main_report.tex` to reflect the real pipeline and results.
