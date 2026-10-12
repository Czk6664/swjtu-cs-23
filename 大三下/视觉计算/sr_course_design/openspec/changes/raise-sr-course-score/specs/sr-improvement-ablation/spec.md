## ADDED Requirements

### Requirement: Edge-loss weight is configurable
The training configuration SHALL expose the edge-loss weight as a YAML-controlled parameter instead of using only a fixed hard-coded value.

#### Scenario: Edge weight is changed in config
- **WHEN** a training config specifies a different `edge_weight`
- **THEN** the combined loss uses that value while preserving existing behavior when the field is omitted

### Requirement: Edge-loss ablation includes multiple settings
The project SHALL support and document more than one edge-loss configuration so the report can analyze whether poor performance is caused by the idea itself or by an overly strong weight.

#### Scenario: Edge ablation is run
- **WHEN** configs for no-edge and multiple edge weights are trained and evaluated
- **THEN** the report can compare PSNR, SSIM, and visual outputs across the ablation settings

### Requirement: Improvement attempts are reported honestly
The report SHALL describe an improvement as exploratory unless it consistently improves quantitative or visual results under comparable settings.

#### Scenario: Improvement underperforms
- **WHEN** an edge-loss or other enhancement experiment performs worse than the baseline
- **THEN** the report states that the attempted improvement did not succeed under the current setting and analyzes likely causes

### Requirement: At least one additional improvement path is planned or prototyped
The project SHALL include either a runnable lightweight additional improvement experiment or a concrete implementation plan for one, such as residual feature attention, multi-scale fusion, frequency-domain loss, perceptual loss, or scheduler-based training improvement.

#### Scenario: Original design component is reviewed
- **WHEN** a reviewer evaluates whether the project proposes its own algorithmic idea
- **THEN** the project provides a concrete mechanism, expected effect, implementation location, and experiment plan rather than only naming a technique

### Requirement: Ablation summaries are generated from metrics
The project SHALL generate ablation comparison tables or figures from CSV metric files rather than manually typed results where feasible.

#### Scenario: Ablation report asset is generated
- **WHEN** ablation CSV files exist
- **THEN** the asset generation script can create a comparison table or chart that matches those CSV values
