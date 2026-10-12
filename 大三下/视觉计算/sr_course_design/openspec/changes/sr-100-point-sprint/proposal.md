## Why

Current course report quality is already in the excellent range, but it still has two visible gaps for a strict full-score review: the implemented IMDN is a simplified IMDN-like model rather than a closer reproduction of the original Information Distillation Block, and the current improvement experiments include honest negative results but do not yet provide a clearly positive self-designed enhancement. This change targets the final 90-to-100-point gap by adding a lower-risk positive enhancement, a closer IMDN reproduction branch, and paper-grade evaluation alignment.

## What Changes

- Add self-ensemble inference for the current best IMDN 50 epoch checkpoint, including flip/rotation transforms, inverse transforms, merged outputs, and PSNR/SSIM comparison against normal inference.
- Add an IDB-IMDN-Lite model branch that more closely follows the original IMDN split-and-fuse information distillation idea while staying runnable under the course CPU constraints.
- Add experiment scripts and configs for IDB-IMDN-Lite training/evaluation, self-ensemble benchmark evaluation, and final asset generation.
- Add paper-grade evaluation alignment materials: protocol alignment table, public IMDN comparison table, and gap attribution table.
- Update report assets and report text to present the new positive enhancement, closer reproduction branch, and reproducibility protocol without overstating novelty.
- Package the new code/config/report changes as an incremental sprint package for running on another machine if needed.

## Capabilities

### New Capabilities
- `sr-self-ensemble-inference`: Covers deterministic test-time augmentation inference for super-resolution models and comparison against normal inference.
- `sr-idb-imdn-reproduction`: Covers a closer IMDN-style Information Distillation Block implementation, training configs, and comparison with the existing simplified IMDN branch.
- `sr-evaluation-protocol-alignment`: Covers standard benchmark protocol alignment, public-result comparison, gap attribution, and report integration for full-score review.

### Modified Capabilities
- None.

## Impact

- Affected source code: `src/models/`, `src/infer.py` or a new inference tool, model registry imports, and smoke/model tests.
- Affected configs/scripts: new IDB-IMDN training configs, self-ensemble evaluation scripts, final experiment runner, and packaging script.
- Affected tools: report asset generation, benchmark summarization, and optional result collection utilities.
- Affected report files: `report/main_report.tex`, `report/figures/`, and final compiled PDF.
- Dependencies should remain lightweight. Self-ensemble should not require new packages. IDB-IMDN-Lite should reuse MindSpore, Pillow, NumPy, PyYAML, and existing evaluation utilities.
