## Context

The project already contains a reproducible MindSpore super-resolution pipeline: paired LR/HR data loading, SRCNN and simplified IMDN/CA-IMDN models, training configs, checkpoint saving, directory inference, PSNR/SSIM evaluation, benchmark scripts, perceptual metrics, report asset generation, and LaTeX report compilation. The latest report is strong by course-design standards, but a strict full-score review can still challenge two points: the main IMDN implementation is simplified, and the current improvement attempts include negative or marginal results rather than a clearly positive enhancement.

This design adds a focused final sprint instead of broad new experiments. The sprint should preserve the existing report's honesty while adding (1) a low-risk positive inference enhancement, (2) a closer IMDN reproduction branch, and (3) a clearer paper-style evaluation protocol alignment.

## Goals / Non-Goals

**Goals:**
- Provide a deterministic self-ensemble inference path for the best IMDN checkpoint and evaluate whether it improves PSNR/SSIM on DIV2K and standard benchmarks.
- Add an IDB-IMDN-Lite model that more closely reflects the original IMDN split-and-fuse Information Distillation Block while staying small enough for course CPU training.
- Add report-ready tables and figures that compare simplified IMDN, IDB-IMDN-Lite, self-ensemble inference, Bicubic, and public IMDN results without overstating equivalence to the original paper.
- Produce an incremental package containing new code, configs, scripts, report changes, and instructions, without bundling large DIV2K data.

**Non-Goals:**
- Do not implement ESRGAN, SR3, StableSR, DiffIR, or MambaIR training.
- Do not claim a novel state-of-the-art algorithm.
- Do not remove existing negative results such as BSD100 underperformance or structure-loss regressions.
- Do not require new heavyweight dependencies beyond the current MindSpore/Pillow/NumPy/YAML/testing stack.

## Decisions

### Decision 1: Implement self-ensemble as a separate inference utility

Self-ensemble inference should live in a dedicated tool such as `tools/run_self_ensemble_eval.py` rather than overloading the normal `src/infer.py` path. The utility should reuse `build_model`, checkpoint loading, image conversion, and evaluation helpers where practical.

Rationale: normal inference must stay simple and stable for existing scripts. Self-ensemble is an experiment-specific inference mode and should produce its own outputs and CSVs under a clear directory such as `results_100pt/self_ensemble/`.

Alternatives considered:
- Add a `--self-ensemble` flag to `src/infer.py`: convenient, but increases the core CLI surface and risks breaking existing one-click scripts.
- Build a separate tool: slightly more duplication, but safer and easier to document as an experiment.

### Decision 2: Use eight deterministic test-time transforms

Self-ensemble should use the identity transform plus combinations of horizontal flip, vertical flip, and 90-degree rotations. Each model output must be inverse-transformed before averaging. The final image should be clipped to valid RGB range and saved with the original filename.

Rationale: this is a standard super-resolution test-time augmentation pattern, deterministic, and likely to provide a small but real gain without retraining.

### Decision 3: Add IDB-IMDN-Lite alongside existing IMDN

The closer reproduction branch should be added as a new model class, not as a replacement for the existing `IMDN`. The new block should split channels into distilled and remaining features across several convolution stages, concatenate distilled features, fuse with a `1x1` convolution, and add a residual connection.

Rationale: the current report relies on the existing simplified IMDN results. Replacing it would destabilize past conclusions. A new `idb_imdn` model name allows clean comparison:
- simplified IMDN: course lightweight baseline
- IDB-IMDN-Lite: closer reproduction of original IMDN structure
- public IMDN: paper-level reference result

### Decision 4: Keep IDB-IMDN-Lite training bounded

IDB-IMDN-Lite should have a smoke config and at least one practical training config, preferably 20 epoch first. A 50 epoch config may be included for external-machine runs, but the sprint should not depend on finishing it locally.

Rationale: training time is the main project constraint. The final report can still benefit from a closer structural reproduction even if the 20 epoch result is used as a comparison point, especially when paired with protocol alignment and honest gap attribution.

### Decision 5: Treat report integration as evidence alignment, not score-chasing language

Report changes should introduce:
- a self-ensemble inference subsection with normal-vs-ensemble metrics;
- an IDB-IMDN-Lite reproduction subsection with model-structure comparison;
- a protocol alignment table comparing public IMDN and this project;
- a gap attribution table explaining remaining performance differences;
- updated conclusion language that frames the new work as course-level rigorous reproduction and enhancement.

Rationale: the report should read like a coherent research document, not like a list of grading patches.

## Risks / Trade-offs

- Self-ensemble may not improve all datasets → Report per-dataset results and preserve negative cases rather than hiding them.
- IDB-IMDN-Lite may train slower or perform below simplified IMDN under limited epochs → Present it as closer structural reproduction, not guaranteed performance improvement.
- Benchmark SSIM implementation may not match public papers → Emphasize PSNR trend and protocol differences; avoid claiming strict public-result equivalence.
- Additional report sections may make the PDF too long → Keep new text focused and replace redundant discussion if needed.
- New model imports can break existing tests → Add smoke tests for output shape and keep old model names unchanged.

## Migration Plan

1. Add new model class and keep current `IMDN`/`CAIMDN` unchanged.
2. Add self-ensemble utility and IDB-IMDN configs without modifying existing result files.
3. Add tests for model shape and self-ensemble transform inversion.
4. Run smoke checks before long experiments.
5. Run self-ensemble evaluation with the existing best checkpoint.
6. Train/evaluate IDB-IMDN-Lite according to available machine time.
7. Generate final report assets, update `main_report.tex`, compile PDF, and build the incremental package.

Rollback is straightforward: the new model, tools, configs, report sections, and result directories are additive. Existing IMDN results and report content remain recoverable by removing the new additions.

## Open Questions

- Whether the other machine should run IDB-IMDN-Lite for 20 epoch only or also 50 epoch depends on available runtime.
- If self-ensemble improves DIV2K but regresses a standard benchmark, the report should decide whether to present it as dataset-dependent rather than a universal best setting.
- If IDB-IMDN-Lite underperforms the simplified IMDN, the report should emphasize reproduction depth and structure comparison rather than performance superiority.
