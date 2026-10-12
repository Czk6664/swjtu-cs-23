## Why

The current super-resolution course design is a runnable MindSpore reproduction, but it is vulnerable under strict grading: the literature review is not current enough, the experiments are under-trained, the only improvement is a weak edge-loss ablation, and the report does not clearly separate reproduced work from original exploratory work.

This change upgrades the project from a minimal runnable loop into a stronger course submission aligned with the six grading criteria: clearer structure, deeper recent literature coverage, more credible experiments, stronger algorithm analysis, better-motivated improvement attempts, and explicit novelty boundaries.

## What Changes

- Expand the report with a grading-oriented structure: literature depth, method analysis, experiment fairness, innovation boundary, limitations, and next-step planning.
- Add recent super-resolution literature coverage, including Transformer-based and diffusion-prior methods from 2021-2024.
- Strengthen the experiment pipeline so SRCNN and IMDN comparisons are fairer and more defensible.
- Add configurable improvement experiments beyond a single fixed edge loss, especially edge-loss weight ablation and training configuration ablation.
- Improve data sampling and reporting so training curves, CSV outputs, visual comparisons, and evaluation figures reflect the full experiment process.
- Reduce reliance on AI-generated diagrams as evidence and emphasize real experimental artifacts.
- Add standard benchmark or benchmark-compatible evaluation support where feasible, while keeping the project CPU-runnable.
- Preserve honesty when an attempted improvement does not outperform the baseline, and turn failed improvement results into critical analysis rather than hiding them.

## Capabilities

### New Capabilities

- `course-report-quality`: Requirements for a high-scoring course report, including structure, figure usage, word count, innovation boundary, and grading-point coverage.
- `sr-literature-positioning`: Requirements for recent SR literature coverage and deeper analysis of representative methods.
- `sr-experiment-rigor`: Requirements for fair, reproducible, and benchmark-aware super-resolution experiments.
- `sr-improvement-ablation`: Requirements for configurable algorithm-improvement experiments and ablation analysis.

### Modified Capabilities

- None.

## Impact

- Affected report files: `report/main_report.tex`, `report/mybib.bib`, `report/figures/*`.
- Affected experiment scripts: `src/train.py`, `src/infer.py`, `src/eval.py`, `tools/generate_report_assets.py`.
- Affected configuration files: `src/configs/*.yaml`.
- Potential new scripts: benchmark preparation/evaluation helpers, experiment comparison helpers, feature/edge visualization helpers.
- Potential new outputs: additional CSV metrics, ablation figures, benchmark result tables, real experiment screenshots or generated evidence figures.
- No breaking API changes are intended; CLI compatibility should be preserved where possible.
