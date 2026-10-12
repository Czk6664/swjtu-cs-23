## ADDED Requirements

### Requirement: Evaluation protocol alignment table
The report SHALL include a protocol alignment table comparing public IMDN evaluation settings and this project's evaluation settings.

#### Scenario: Protocol table covers core settings
- **WHEN** the report is updated
- **THEN** the protocol table SHALL cover scale, training data, test datasets, color channel, border crop, metrics, model structure, training budget, and evaluation script differences

#### Scenario: Protocol limits are explicit
- **WHEN** public IMDN results are compared with this project's results
- **THEN** the report SHALL state that the comparison is for positioning and gap analysis, not a claim of strict reproduction equivalence

### Requirement: Public-result comparison and gap attribution
The report SHALL include public-result comparison and gap attribution materials for simplified IMDN and IDB-IMDN-Lite.

#### Scenario: Public comparison table is present
- **WHEN** report tables are generated
- **THEN** the report SHALL include public IMDN benchmark references alongside this project's comparable model results where available

#### Scenario: Gap attribution is present
- **WHEN** a model underperforms public IMDN or Bicubic on a dataset
- **THEN** the report SHALL attribute the gap to concrete factors such as structure simplification, training budget, data coverage, CPU constraints, or metric implementation differences

### Requirement: Final full-score report integration
The final report SHALL integrate new sprint results without weakening existing honest negative-result analysis.

#### Scenario: BSD100 negative result is preserved
- **WHEN** report benchmark discussion is updated
- **THEN** the BSD100 result where IMDN underperforms Bicubic in PSNR SHALL remain visible and discussed as a limitation

#### Scenario: Self-designed work is bounded
- **WHEN** the report describes self-ensemble inference, IDB-IMDN-Lite, or CA-IMDN
- **THEN** it SHALL distinguish course-level implementation/design work from prior published methods

#### Scenario: PDF can be compiled
- **WHEN** report integration is complete
- **THEN** `xelatex + bibtex + xelatex + xelatex` SHALL produce `report/main_report.pdf` without LaTeX errors, undefined citations, or undefined references

### Requirement: Incremental sprint package
The system SHALL package the final sprint additions for transfer to another machine without including large DIV2K data.

#### Scenario: Patch archive is created
- **WHEN** the packaging script runs
- **THEN** it SHALL create an archive containing new/modified source code, configs, scripts, report source, report PDF, figures, and instructions

#### Scenario: Large training data is excluded
- **WHEN** the patch archive is created
- **THEN** it SHALL exclude DIV2K training/validation image directories and any unnecessary large result directories
