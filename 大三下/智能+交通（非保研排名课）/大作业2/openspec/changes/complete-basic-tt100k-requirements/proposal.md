## Why

The current project already has a working YOLO11n + TT100K experiment pipeline and a drafted report, but the selected 12-class configuration only contains 8 classes with actual labeled samples. This creates a direct compliance risk against the course requirement to train and test on more than 10 target classes.

This change focuses the next phase on making the basic assignment deliverable defensible before adding more high-level system features.

## What Changes

- Re-select a TT100K traffic-sign class subset with at least 10 classes that each have nonzero annotated objects in the generated YOLO dataset.
- Regenerate the YOLO-format dataset and dataset configuration so the class list, labels, statistics, and report all describe the same effective task.
- Re-run YOLO11n training and validation on the compliant 10+ class TT100K subset.
- Export updated experiment assets for the course report, including metrics, training curves, confusion matrices, and validation prediction examples.
- Update the LaTeX report so the dataset section, experiment tables, figures, failure analysis, and improvement discussion all match the final compliant experiment.
- Fill remaining report placeholders such as student information, team member names, class, and supervisor.
- Keep the high-level workbench and traffic-flow prediction integration out of scope except for optional references after the basic requirements are stable.

## Capabilities

### New Capabilities
- `basic-tt100k-compliance`: Ensures the basic course assignment can be verified as a TT100K-based 10+ class traffic-sign detection experiment with aligned dataset statistics, training results, and report evidence.

### Modified Capabilities

None.

## Impact

- Affected code and configs:
  - `traffic_sign_detection/src/tt100k/classes.py`
  - `traffic_sign_detection/configs/dataset/tt100k.yaml`
  - `traffic_sign_detection/scripts/prepare_tt100k.py` and related dataset preparation flow if class selection or reporting support needs adjustment
  - `traffic_sign_detection/train.py`, `val.py`, and experiment configs as execution entrypoints
- Affected generated data and experiment assets:
  - `traffic_sign_detection/data/tt100k_yolo`
  - new or updated experiment run directories
  - `课程设计模版_2026年/figures/tt100k_experiment`
- Affected documentation:
  - `课程设计模版_2026年/main_report.tex`
  - supporting summaries under `solution_design/` only if they are referenced by the basic report
- No public API or deployed service contract changes are expected.
