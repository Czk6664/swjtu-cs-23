## Context

The project is a MindSpore-based super-resolution course design under `sr_course_design/`. It already contains a runnable CPU loop for SRCNN, IMDN, bicubic inference, PSNR/SSIM evaluation, report figures, and a compiled LaTeX report.

The current submission would likely pass as a minimal reproduction, but it is not yet strong under strict grading. The report has many generated schematic figures, limited recent literature, a simplified IMDN implementation, short training runs, a fixed edge-loss experiment that underperforms the no-edge model, and no explicit section separating prior work from the project's own work.

The target is not to fake a perfect result. The target is to improve the project so it can defend itself against the six grading points: logic and presentation, recent literature, experiment detail, algorithm understanding, original improvement, and distinction between existing and original work.

## Goals / Non-Goals

**Goals:**

- Produce a stronger report with explicit grading coverage, deeper literature analysis, and clearer novelty boundaries.
- Add or improve code paths that make the experiments more credible: fair configs, multi-patch sampling, configurable loss weights, scheduler support, and richer output artifacts.
- Add ablations that can be run within local CPU constraints while still showing meaningful experimental reasoning.
- Add benchmark-compatible evaluation support where datasets are available, without requiring the project to download large datasets automatically.
- Make figures and tables reflect real experiment artifacts wherever possible.
- Preserve reproducibility by writing exact commands, configs, CSV outputs, and generated figures.

**Non-Goals:**

- Reproduce large-scale SR state of the art such as HAT, StableSR, DiffIR, or SeeSR training.
- Guarantee that the new improvement beats Bicubic or published IMDN results under CPU-limited training.
- Add GPU-only dependencies or workflows that make the existing CPU loop unusable.
- Replace the project with a different framework or a large third-party training system.
- Hide negative results or overstate the novelty of edge loss.

## Decisions

### Decision 1: Treat the work as a rigorous course reproduction plus exploratory improvement

The report will frame the project as a reproducible MindSpore SR pipeline with an exploratory edge/structure enhancement branch. This is more defensible than claiming a novel state-of-the-art method.

Alternative considered: Present edge loss as the main innovation. Rejected because the current fixed edge-loss experiment performs worse than the no-edge model and edge losses are already common in SR literature.

### Decision 2: Improve experiments through fairness and ablation before chasing model scale

Implementation should prioritize fairer comparison and better experimental design:

- SRCNN and IMDN configs should be made more comparable where runtime allows.
- Training should support multiple random patches per source image.
- `CombinedLoss` should expose `edge_weight` through config.
- Training should optionally support learning-rate scheduling.
- Assets should plot complete intended runs or explicitly label selected runs.

Alternative considered: Increase IMDN width/epochs only. Rejected as the sole strategy because it may take too long on CPU and still leaves the grading criticism about experiment design unresolved.

### Decision 3: Add benchmark-compatible evaluation without forcing dataset downloads

The code should support evaluating Set5, Set14, BSD100, or Urban100 if the user places paired LR/HR data in the expected directory format. The report can include benchmark planning and, when data exists, benchmark tables.

Alternative considered: Automatically download benchmarks. Rejected because dataset hosting and network reliability are outside the current project constraints.

### Decision 4: Strengthen literature through representative recent methods, not shallow name-dropping

The report should add a small but meaningful timeline/comparison of recent SR methods:

- SwinIR for Transformer-based restoration.
- HAT and/or DAT for stronger attention-based SR.
- StableSR, DiffIR, and/or SeeSR for diffusion-prior and semantic-aware real-world SR.
- Real-ESRGAN as a real-world degradation/generative baseline.

Each method should be used to explain a design axis: reconstruction fidelity, attention range, real degradation, diffusion prior, semantic fidelity, or efficiency.

Alternative considered: Add many references with one-sentence summaries. Rejected because the scoring criticism is about depth, not citation count alone.

### Decision 5: Keep generated diagrams but subordinate them to real evidence

Generated figures may remain as conceptual illustrations, but report claims should rely on real curves, CSV-derived tables, visual comparisons, config tables, and ablation figures.

Alternative considered: Remove all generated figures. Rejected because some schematic diagrams improve readability and the course rubric values being graphically rich.

## Risks / Trade-offs

- CPU runtime may prevent long training runs -> Use staged configs: quick smoke, fair short run, and optional extended run.
- New ablations may still not beat Bicubic -> Report them honestly as evidence about training budget, loss weight sensitivity, and model capacity.
- Adding too many literature sections may bloat the report -> Use a compact comparison table plus focused paragraphs on 3-5 representative methods.
- Standard benchmark data may not be available locally -> Add benchmark-compatible commands and report planning; include results only when data exists.
- More figures can make the report feel padded -> Prefer fewer real evidence figures over many decorative diagrams.
- More config options can complicate scripts -> Keep defaults backward-compatible and document new fields clearly.

## Migration Plan

1. Add configuration fields with safe defaults so existing YAML files continue to run.
2. Add new configs for fair comparison and ablation rather than overwriting existing experiment records.
3. Regenerate figures from CSV outputs after each completed run.
4. Update report and bibliography after experiment outputs exist.
5. Compile the PDF and verify references, captions, and table layout.

Rollback is straightforward: keep old configs/results intact and isolate new experiments under distinct filenames.

## Open Questions

- How much wall-clock time is acceptable for the extended training run on the user's machine?
- Are Set5/Set14/BSD100/Urban100 datasets available locally, or should the report only include benchmark-compatible commands and future-work planning?
- Should the final report keep all generated schematic figures, or trim to the most useful 3-4 conceptual figures?
- Can the user provide real team member names and concrete division of labor for the final report?
