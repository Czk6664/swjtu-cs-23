## ADDED Requirements

### Requirement: System SHALL provide TT100K-based multi-target traffic sign detection
The system SHALL provide a traffic target detection module based on TT100K that supports detection of at least 10 traffic sign classes and outputs bounding boxes, class labels, confidence scores, and experiment metrics for the selected model.

#### Scenario: Detect supported traffic sign categories
- **WHEN** the user runs the traffic target detection experiment on the TT100K subset used by the project
- **THEN** the system SHALL detect no fewer than 10 traffic sign categories and produce per-image detection outputs

#### Scenario: Export quantitative evaluation metrics
- **WHEN** training and validation complete
- **THEN** the system SHALL provide Precision, Recall, mAP50, and mAP50-95 metrics for the detection model

### Requirement: System SHALL document the chosen recent target detection model
The system SHALL identify one target detection model from the last three years as the primary research object and describe its model structure, computational principle, and selection rationale in the solution artifacts.

#### Scenario: Explain model selection
- **WHEN** the system design or report references the target detection module
- **THEN** it SHALL state that YOLO11n is the primary detection model and explain why it is suitable for the TT100K task and available hardware constraints

#### Scenario: Explain model computation flow
- **WHEN** the user reads the technical design or report
- **THEN** the artifacts SHALL describe the backbone feature extraction, multi-scale feature fusion, detection head output, and optimization objective at a level suitable for coursework reporting

### Requirement: System SHALL surface qualitative detection evidence
The system SHALL provide qualitative examples that show how the detection module behaves in realistic traffic scenes, including both successful detections and known failure cases.

#### Scenario: Show representative prediction cases
- **WHEN** the user opens the experiment presentation or workbench
- **THEN** the system SHALL include representative validation images with predicted boxes and labels

#### Scenario: Explain observed weaknesses
- **WHEN** qualitative results are presented
- **THEN** the system SHALL identify at least one observed issue such as small-object misses, occlusion sensitivity, or background interference
