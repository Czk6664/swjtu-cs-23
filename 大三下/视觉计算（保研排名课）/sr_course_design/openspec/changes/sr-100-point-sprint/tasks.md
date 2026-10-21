## 1. Self-Ensemble Inference

- [x] 1.1 Add deterministic geometric transform and inverse-transform utilities for identity, flips, rotations, and flip-rotation combinations.
- [x] 1.2 Add a self-ensemble inference tool that loads an existing learned-model checkpoint, applies all transforms, inverse-transforms outputs, averages predictions, and saves one output image per input.
- [x] 1.3 Add normal-vs-self-ensemble evaluation workflow that produces per-image CSVs and summary CSVs for DIV2K eval and available standard benchmarks.
- [x] 1.4 Add self-ensemble smoke test coverage for transform inversion, output shape, and output file creation.
- [x] 1.5 Generate report-ready self-ensemble metric chart and visual comparison grid from real outputs.

## 2. IDB-IMDN-Lite Reproduction Branch

- [x] 2.1 Implement an IDB-style distillation block with staged distilled/remaining channel splits, feature concatenation, `1x1` fusion, and residual connection.
- [x] 2.2 Add an `IDBIMDN` model class that uses the new block and preserves configurable scale, feature width, and block count.
- [x] 2.3 Register `idb_imdn` in training and inference model builders without changing existing `imdn` and `ca_imdn` behavior.
- [x] 2.4 Add IDB-IMDN-Lite smoke and 20 epoch configs using the existing DIV2K data layout; optionally add a 50 epoch external-machine config.
- [x] 2.5 Add model shape and parameter-count checks for IDB-IMDN-Lite.
- [x] 2.6 Run IDB-IMDN-Lite smoke training/inference locally, then prepare the longer run for the external machine if local runtime is too high.

## 3. Experiment Orchestration

- [x] 3.1 Add a final sprint Windows runner that can run smoke checks, self-ensemble evaluation, IDB-IMDN-Lite training/evaluation, asset generation, and report compilation by stage.
- [x] 3.2 Ensure all sprint outputs are written under `results_100pt/` or clearly named checkpoint/log paths to avoid overwriting existing 90-point results.
- [x] 3.3 Add result summarization for normal IMDN, self-ensemble IMDN, simplified IMDN, IDB-IMDN-Lite, Bicubic, and public IMDN comparison inputs.
- [x] 3.4 Add clear failure messages for missing checkpoint, missing benchmark data, missing MindSpore, or unavailable long-training results.

## 4. Report Integration

- [x] 4.1 Add a self-ensemble inference subsection with normal-vs-ensemble metrics, visual evidence, and dataset-dependent caveats.
- [x] 4.2 Add an IDB-IMDN-Lite reproduction subsection comparing simplified IMDN, IDB-IMDN-Lite, and original IMDN structure.
- [x] 4.3 Add an evaluation protocol alignment table covering scale, datasets, channel, crop, metrics, model structure, training budget, and evaluation implementation.
- [x] 4.4 Add a gap attribution table explaining differences from public IMDN benchmark results.
- [x] 4.5 Preserve existing negative-result analysis, including BSD100 PSNR underperformance and structure-loss regressions.
- [x] 4.6 Update conclusion language to describe the sprint as course-level rigorous reproduction and enhancement, not a new state-of-the-art algorithm.

## 5. Verification and Packaging

- [x] 5.1 Run targeted tests for models, inference smoke, metrics, and new self-ensemble utilities.
- [x] 5.2 Compile `report/main_report.tex` with `xelatex + bibtex + xelatex + xelatex` and verify no LaTeX errors, undefined citations, or undefined references remain.
- [x] 5.3 Create an incremental 100-point sprint package containing new/modified code, configs, scripts, report source/PDF, figures, CSV summaries, and run instructions.
- [x] 5.4 Verify the package excludes large DIV2K data and unnecessary large result folders.
- [x] 5.5 Add or update README/CHECKLIST instructions describing what to run on another machine and which result folders/checkpoints to bring back.
