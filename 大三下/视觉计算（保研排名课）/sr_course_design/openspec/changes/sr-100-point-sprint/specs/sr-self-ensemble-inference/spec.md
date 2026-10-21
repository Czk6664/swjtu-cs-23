## ADDED Requirements

### Requirement: Deterministic self-ensemble inference
The system SHALL provide a deterministic self-ensemble inference workflow for learned super-resolution models using image flips and rotations.

#### Scenario: Self-ensemble output is generated
- **WHEN** the self-ensemble workflow is run on an LR image directory with a valid learned-model checkpoint
- **THEN** the system SHALL save one super-resolved output image per input image in the configured output directory

#### Scenario: Transform inversion is applied
- **WHEN** the workflow applies a geometric transform before model inference
- **THEN** the corresponding model output SHALL be inverse-transformed before output averaging

#### Scenario: Output shape is valid
- **WHEN** an input image has width `W`, height `H`, and scale `S`
- **THEN** the self-ensemble output SHALL have width `W*S` and height `H*S`

### Requirement: Normal-vs-ensemble metric comparison
The system SHALL compare normal inference and self-ensemble inference with the same PSNR/SSIM evaluation protocol.

#### Scenario: Comparison CSV is produced
- **WHEN** both normal inference outputs and self-ensemble outputs exist for the same target HR directory
- **THEN** the system SHALL produce per-image CSV files and a summary CSV containing average PSNR and SSIM for both modes

#### Scenario: Positive and negative results are preserved
- **WHEN** self-ensemble improves one dataset but regresses another dataset
- **THEN** the report assets SHALL preserve both outcomes instead of filtering failed cases

### Requirement: Self-ensemble report assets
The system SHALL generate report-ready assets for self-ensemble inference results.

#### Scenario: Bar chart is generated
- **WHEN** normal-vs-ensemble summary CSV files are available
- **THEN** the asset generation workflow SHALL create a non-empty chart comparing PSNR/SSIM across inference modes

#### Scenario: Visual grid is generated
- **WHEN** representative output images are available
- **THEN** the asset generation workflow SHALL create a visual comparison grid containing LR/Bicubic/normal IMDN/self-ensemble/HR where the available outputs permit it
