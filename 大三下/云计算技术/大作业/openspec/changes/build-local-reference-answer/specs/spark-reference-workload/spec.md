## ADDED Requirements

### Requirement: SparkApplication template
The final project SHALL provide a SparkApplication YAML template compatible with Spark Operator on Huawei Cloud CCE.

#### Scenario: SparkApplication uses replaceable image
- **WHEN** the SparkApplication YAML is reviewed
- **THEN** it contains a replaceable teacher-provided SWR PySpark image value and sets executor instances to 2 by default

### Requirement: Data cleaning workload
The Spark workload SHALL load a dataset, print schema and sample rows, calculate missing-value ratios, and apply at least two missing-value handling strategies.

#### Scenario: Cleaning output is report-ready
- **WHEN** the Spark analysis script runs successfully
- **THEN** it emits schema, first five rows, missing-value ratios, before/after row counts, and basic statistics

### Requirement: SQL analysis workload
The Spark workload SHALL include at least four statistical analyses covering GROUP BY, Top-N ordering, time trend analysis, and either JOIN or window functions.

#### Scenario: Required SQL categories are present
- **WHEN** the analysis script is reviewed
- **THEN** the four required query categories are implemented with named output sections suitable for screenshots

### Requirement: Performance comparison
The final project SHALL include a performance comparison workflow for Pandas, PySpark with one executor, and PySpark with two executors.

#### Scenario: Performance chart can be generated
- **WHEN** the comparison script is run with recorded timings
- **THEN** it creates a chart or tabular output suitable for Amdahl-law discussion in the report
