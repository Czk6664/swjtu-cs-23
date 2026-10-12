## ADDED Requirements

### Requirement: IDB-IMDN-Lite model branch
The system SHALL provide an IDB-IMDN-Lite model branch that more closely follows the original IMDN information distillation structure than the current simplified IMDN.

#### Scenario: Model can be constructed
- **WHEN** the model builder receives the model name `idb_imdn`
- **THEN** it SHALL construct an IDB-IMDN-Lite network with configurable scale, feature width, and block count

#### Scenario: Model output shape matches super-resolution scale
- **WHEN** IDB-IMDN-Lite receives a tensor of shape `(N, 3, H, W)` with scale `S`
- **THEN** it SHALL return a tensor of shape `(N, 3, H*S, W*S)`

### Requirement: Split-and-fuse distillation block
The IDB-IMDN-Lite branch SHALL include a block that splits distilled and remaining feature channels across multiple stages and fuses the distilled features.

#### Scenario: Distilled features are concatenated
- **WHEN** an IDB block processes an input feature tensor
- **THEN** it SHALL concatenate multiple distilled feature groups before applying a fusion convolution

#### Scenario: Residual connection is preserved
- **WHEN** an IDB block finishes feature fusion
- **THEN** it SHALL add the block input to the fused output before returning the block result

### Requirement: IDB-IMDN experiment configs
The system SHALL provide training configs for IDB-IMDN-Lite experiments that are compatible with the existing training pipeline.

#### Scenario: Smoke config exists
- **WHEN** a user wants to validate environment and model wiring quickly
- **THEN** the project SHALL provide a smoke or short-run IDB-IMDN-Lite config that can run with a small training subset

#### Scenario: Course experiment config exists
- **WHEN** a user wants to train IDB-IMDN-Lite for report comparison
- **THEN** the project SHALL provide at least one practical 20 epoch config using the existing DIV2K layout

### Requirement: IDB-IMDN comparison evidence
The system SHALL generate metrics and report evidence comparing IDB-IMDN-Lite with simplified IMDN and public IMDN references.

#### Scenario: IDB metrics are summarized
- **WHEN** IDB-IMDN-Lite evaluation CSVs are available
- **THEN** the project SHALL summarize PSNR/SSIM and include the result in report-ready tables

#### Scenario: Structural comparison is reported
- **WHEN** the report is updated
- **THEN** it SHALL describe how IDB-IMDN-Lite differs from the existing simplified IMDN and from the original public IMDN
