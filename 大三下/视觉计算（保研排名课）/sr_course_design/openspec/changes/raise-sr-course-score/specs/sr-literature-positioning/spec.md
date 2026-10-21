## ADDED Requirements

### Requirement: Literature review includes recent representative SR methods
The report SHALL cite and analyze representative recent super-resolution methods from 2021-2024, including at least one Transformer-based method and at least one diffusion-prior or real-world generative SR method.

#### Scenario: Recent literature coverage is checked
- **WHEN** a reviewer checks the bibliography and related-work section
- **THEN** the report includes recent methods such as SwinIR, HAT or DAT, Real-ESRGAN, StableSR, DiffIR, or SeeSR in addition to classic SRCNN, IMDN, ESRGAN, and SR3

### Requirement: Three or more representative papers receive deeper analysis
The report SHALL provide deeper method-level analysis for at least three representative papers rather than only one-paragraph summaries.

#### Scenario: Paper depth is evaluated
- **WHEN** a reviewer evaluates whether representative papers were read carefully
- **THEN** at least three methods include discussion of their core mechanism, motivation, strengths, weaknesses, and relation to the project design

### Requirement: Literature positioning explains why IMDN remains the implementation target
The report SHALL explain why a lightweight IMDN-style model is selected for implementation despite newer Transformer and diffusion methods.

#### Scenario: Implementation choice is challenged
- **WHEN** a reviewer asks why the project does not reproduce HAT, StableSR, or DiffIR
- **THEN** the report justifies IMDN using CPU constraints, MindSpore course feasibility, reproducibility, and the difference between research survey targets and implementation targets

### Requirement: Literature discussion connects methods to evaluation trade-offs
The report SHALL explain the trade-off between distortion-oriented metrics such as PSNR/SSIM and perception-oriented quality in GAN and diffusion SR methods.

#### Scenario: Metric choice is challenged
- **WHEN** a reviewer asks why PSNR/SSIM are insufficient
- **THEN** the report explains perception-distortion trade-offs and identifies LPIPS/NIQE or visual comparison as relevant complementary evidence
