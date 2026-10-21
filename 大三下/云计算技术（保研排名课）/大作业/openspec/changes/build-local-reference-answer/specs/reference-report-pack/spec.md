## ADDED Requirements

### Requirement: Final project README
The final project SHALL include a README that explains how to run local Docker, build images, push to SWR, apply CCE manifests, run Spark, and gather evidence.

#### Scenario: README guides the full workflow
- **WHEN** a teacher opens the README
- **THEN** it lists commands and placeholders for local execution, Huawei Cloud deployment, Spark execution, and report evidence capture

### Requirement: Report scaffold
The final project SHALL include a report scaffold using 程泽凯，王晨羽, 2023112621,2023114337, and 2023-04班 as the identity information.

#### Scenario: Report scaffold contains required sections
- **WHEN** the report scaffold is opened
- **THEN** it contains cover information, Huawei Cloud environment, first-part tasks 1-6, Spark direction-A records, summary, and appendix sections

### Requirement: Screenshot checklist
The final project SHALL include a screenshot checklist aligned with the scoring rubric.

#### Scenario: Checklist covers mandatory evidence
- **WHEN** the checklist is reviewed
- **THEN** it includes local compose evidence, SWR image evidence, CCE node evidence, Pod and ELB evidence, Redis PVC evidence, ConfigMap Volume evidence, HPA evidence, and Spark evidence

### Requirement: Safe placeholder policy
The final project SHALL document that real cloud credentials and passwords must not be committed.

#### Scenario: Secrets are excluded
- **WHEN** reference files are reviewed
- **THEN** AK/SK, kubeconfig, real Redis password, OBS credentials, and SWR login tokens are represented only by placeholders or local environment variables
