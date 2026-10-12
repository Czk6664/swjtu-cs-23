# Final Improvement Summary

## Completed Improvements

- Added multi-patch training support through `patches_per_image`.
- Added configurable edge-loss weights through `edge_weight`.
- Added quick fair comparison and edge-weight ablation configs.
- Ran quick SRCNN/IMDN/edge-weight training experiments and full DIV2K validation inference/evaluation.
- Added benchmark-compatible evaluation helper for Set5/Set14/BSD100/Urban100 style folders.
- Regenerated evidence figures from CSV and real inference outputs.
- Added recent SR literature coverage for Transformer, GAN, and diffusion-prior methods.
- Added report sections for grading criteria, work boundaries, exploratory improvement, limitations, and next-step planning.
- Recompiled the PDF and verified there are no undefined citations or references.
- Ran focused tests successfully.
- Full `pytest` collection is still blocked by existing Windows permission-denied pytest cache directories (`pytest-cache-files-*`), not by project assertions; focused test files pass.

## Remaining Submission Edits

- Replace `成员 1/2/3（最终提交前填写真实姓名）` with actual names and final division of labor.
- Longer training and standard benchmark results can further improve confidence if more runtime is available.
- LPIPS/NIQE or subjective user-study metrics are still future work.
