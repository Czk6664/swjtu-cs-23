## ADDED Requirements

### Requirement: Effective TT100K Class Subset
The project SHALL define a TT100K detection class subset with at least 10 effective target classes, where every selected class has nonzero annotated objects after conversion to YOLO labels.

#### Scenario: Converted labels contain at least 10 nonempty classes
- **WHEN** the generated YOLO label files are scanned across train, validation, and test splits
- **THEN** at least 10 selected class IDs have one or more bounding boxes

#### Scenario: Empty configured classes are not reported as trained targets
- **WHEN** the final dataset configuration and report class table are reviewed
- **THEN** no class with zero generated labels is counted toward the course requirement

### Requirement: Dataset Statistics Are Reproducible
The project SHALL provide reproducible dataset statistics for the final TT100K subset, including image counts, label counts, and per-class object counts for train, validation, and test splits.

#### Scenario: Split statistics are available
- **WHEN** the final dataset preparation flow completes
- **THEN** the project exposes the number of images and label files in train, validation, and test splits

#### Scenario: Per-class counts are available
- **WHEN** the final YOLO labels are scanned
- **THEN** the project can report per-class object counts for each split and for the full dataset

### Requirement: Final YOLO11n Experiment Matches The Compliant Dataset
The project SHALL train and validate YOLO11n on the final compliant TT100K subset and SHALL keep the final metrics, weights, and visual assets aligned with that dataset.

#### Scenario: Final metrics are produced
- **WHEN** the final YOLO11n validation completes
- **THEN** the experiment output includes Precision, Recall, mAP50, and mAP50-95 for the compliant class subset

#### Scenario: Final visual assets are produced
- **WHEN** the final experiment assets are exported
- **THEN** the report has access to training curves, a confusion matrix, and validation prediction examples from the same final run

#### Scenario: Historical runs are not used as final evidence
- **WHEN** old experiment results differ from the final class subset
- **THEN** they are either removed from the final evidence path or clearly labeled as historical references

### Requirement: Basic Report Is Internally Consistent
The final course report SHALL present a consistent basic assignment narrative covering recent algorithm research, YOLO11n structure and computation principles, TT100K 10+ class training/testing, multi-target recognition results, problem analysis, and improvement ideas.

#### Scenario: Report class description matches dataset config
- **WHEN** the report dataset section is compared with the final dataset configuration
- **THEN** the class names, class count, and class mapping are consistent

#### Scenario: Report metrics match experiment outputs
- **WHEN** the report experiment tables are compared with the final `results.csv` or validation output
- **THEN** the reported Precision, Recall, mAP50, and mAP50-95 values match the final experiment

#### Scenario: Report figures match final assets
- **WHEN** the compiled PDF is inspected
- **THEN** the training curves, confusion matrix, and prediction examples correspond to the final compliant experiment

#### Scenario: Report placeholders are resolved
- **WHEN** the final LaTeX source is searched for placeholders
- **THEN** student information, team member names, class, and supervisor fields no longer contain placeholder values such as `待补充`, `成员A`, or `XXX`

### Requirement: Basic Scope Takes Priority Over Optional High-Level Features
The project SHALL treat high-level situation-analysis features as optional until the basic TT100K 10+ class detection report is complete.

#### Scenario: Workbench updates are deferred
- **WHEN** implementation tasks are selected for this change
- **THEN** workbench changes are excluded unless they directly support the basic report evidence

#### Scenario: Traffic-flow prediction is not required for basic completion
- **WHEN** the basic assignment deliverable is evaluated
- **THEN** completion does not depend on traffic-flow prediction or image-flow fusion functionality
