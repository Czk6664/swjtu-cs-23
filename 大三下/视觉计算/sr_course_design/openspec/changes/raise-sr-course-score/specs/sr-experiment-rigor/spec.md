## ADDED Requirements

### Requirement: Experiments are reproducible through commands and configs
The project SHALL provide reproducible commands and configuration files for every reported experiment, including training, inference, evaluation, and figure generation.

#### Scenario: Experiment is rerun from report
- **WHEN** a reviewer follows the commands listed in the report or README
- **THEN** the project can regenerate the corresponding checkpoint, CSV metrics, prediction images, and report figures for that experiment

### Requirement: Learned-model comparisons are made fairer
The project SHALL add fairer comparison configs for SRCNN and IMDN so that reported comparisons do not depend only on mismatched epoch counts or batch sizes unless clearly labeled as constrained runs.

#### Scenario: Baseline fairness is inspected
- **WHEN** a reviewer compares SRCNN and IMDN settings
- **THEN** the report either uses comparable training settings or explicitly labels differences and explains their impact

### Requirement: Training sample coverage can be increased
The training pipeline SHALL support generating multiple aligned random patches per source image so that training coverage can be increased without changing the dataset layout.

#### Scenario: Multi-patch sampling is enabled
- **WHEN** a config sets the number of patches per image above one
- **THEN** the training dataset contains multiple random LR/HR patch pairs per eligible source image

### Requirement: Evaluation supports benchmark-compatible datasets
The project SHALL support evaluating paired LR/HR datasets beyond DIV2K when they follow the existing directory convention, including Set5, Set14, BSD100, or Urban100 if available locally.

#### Scenario: Benchmark dataset is provided
- **WHEN** a benchmark split is placed under a configured directory with matching `LR/` and `HR/` filenames
- **THEN** the existing inference and evaluation commands can produce method outputs and CSV metrics for that benchmark

### Requirement: Report figures use complete and labeled experiment records
The report asset generation SHALL avoid silently selecting only the last rows of a log unless the figure title or caption clearly states the selection.

#### Scenario: Training curve is regenerated
- **WHEN** the training curve figure is generated from CSV logs
- **THEN** the plotted epoch range is either the full intended run or explicitly labeled as a selected run segment
