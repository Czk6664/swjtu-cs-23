## ADDED Requirements

### Requirement: Report covers the six grading criteria explicitly
The report SHALL include content that maps directly to all six course grading criteria: logical structure and visual richness, recent literature, detailed experiments, algorithm understanding, original improvement, and separation of prior work from original work.

#### Scenario: Grading criteria can be audited
- **WHEN** a reviewer checks the final report against the six grading criteria
- **THEN** each criterion has a corresponding section, table, figure, or paragraph that directly supports it

### Requirement: Report distinguishes evidence figures from conceptual figures
The report SHALL distinguish real experiment evidence from conceptual schematic figures, and SHALL NOT rely on AI-generated schematic figures as proof of experimental results.

#### Scenario: Figure evidence is reviewed
- **WHEN** a reviewer inspects the figures and captions
- **THEN** CSV-derived curves, metric tables, visual comparisons, and real outputs are identifiable as experimental evidence, while schematic figures are described as explanatory diagrams

### Requirement: Report includes clear novelty and boundary statements
The report SHALL include a section that clearly states which parts are reproduced from existing work, which parts are course-level implementation choices, and which parts are the project's own exploratory improvement.

#### Scenario: Novelty claim is checked
- **WHEN** a reviewer asks what is original in the project
- **THEN** the report identifies the MindSpore reproduction pipeline, configurable ablation setup, and exploratory loss experiments without overstating them as new SR algorithms

### Requirement: Report includes a defensible limitations and next-plan section
The report SHALL include limitations and next-step planning that directly respond to under-training, benchmark coverage, metric coverage, and failed improvement risks.

#### Scenario: Negative results are challenged
- **WHEN** a reviewer notices that Bicubic outperforms the learned models
- **THEN** the report explains the training budget, sampling coverage, model capacity, and planned corrective experiments rather than hiding the result

### Requirement: Report uses concrete team contribution information
The report SHALL replace placeholder team roles with concrete member names or identifiers and specific contributions before final submission.

#### Scenario: Team section is reviewed
- **WHEN** a reviewer reads the team contribution section
- **THEN** the section does not contain generic placeholders such as "成员 A/B/C" and describes concrete work done by each member
