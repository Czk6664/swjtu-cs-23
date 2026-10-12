## Context

The project currently contains a functioning TT100K-to-YOLO pipeline, YOLO11n training outputs, exported report figures, and a drafted LaTeX report. The strongest completed experiment is the 704-pixel, 50-epoch YOLO11n run, but it is based on the current nominal 12-class subset.

The current class configuration is not fully compliant with the course requirement because four configured classes have zero labeled objects after conversion. The final basic assignment must therefore be rebuilt around an effective 10+ class subset where every reported class is present in the generated labels and participates in training and validation.

The intended stakeholder is the course evaluator. The deliverable must be easy to verify from the report and project files without relying on hidden assumptions.

## Goals / Non-Goals

**Goals:**

- Produce a TT100K detection task with at least 10 effective classes, where each class has nonzero annotated objects in the generated YOLO labels.
- Keep YOLO11n as the focused model for structure and computation-principle analysis.
- Re-run training and validation so quantitative metrics, confusion matrices, and prediction examples correspond to the compliant class subset.
- Update the report so it presents one consistent story: class selection, dataset statistics, model configuration, experiment results, failure analysis, and improvement ideas.
- Preserve reproducibility by keeping scripts, configs, commands, and output paths clear.

**Non-Goals:**

- Do not expand the basic deliverable into a vehicle/pedestrian multi-dataset perception system.
- Do not redesign the high-level situation-analysis workbench during this phase.
- Do not attempt end-to-end fusion between TT100K detection and traffic-flow prediction.
- Do not introduce a new detector family unless YOLO11n training becomes impossible.

## Decisions

### Decision 1: Select classes from actual annotation frequency

The compliant class subset will be selected from raw TT100K categories that have real object counts in `annotations_all.json`, then verified again after YOLO conversion by scanning label files.

Rationale: the course requirement is about training and testing on more than 10 target classes. A class name in `tt100k.yaml` is not sufficient if the generated labels contain zero boxes for that class.

Alternative considered: keep the current 12 configured classes and explain that some classes are empty. This is rejected because it leaves a visible compliance gap.

### Decision 2: Prefer high-frequency TT100K classes for the final subset

The final subset should use at least 10, preferably 12, classes with enough samples to support train/val/test evaluation. Candidate classes should come from high-frequency categories such as `pn`, `pne`, `i5`, `p11`, `pl40`, `pl50`, `pl80`, `p26`, `pl60`, `i4`, `pl30`, `pl5`, `i2`, and `p5`, subject to clear naming in the report.

Rationale: rare classes make confusion matrices unstable and make per-class discussion weak. Higher-frequency classes make the final report easier to defend.

Alternative considered: choose visually familiar classes only. This is weaker because familiar classes may have poor or zero sample coverage in the local TT100K release.

### Decision 3: Treat the rebuilt dataset as the final basic experiment source of truth

After the class subset changes, existing `exp_A`, `exp_B`, and `exp_C` results become historical references rather than final evidence. The final report should cite only the new compliant experiment as the main result, optionally retaining old runs as motivation for input-size or training-duration choices if they remain comparable.

Rationale: metrics from different class spaces are not directly comparable. Keeping old numbers as final results would make the report internally inconsistent.

Alternative considered: keep old figures and only update text. This is rejected because the final class count and metrics would not match.

### Decision 4: Keep the report focused on the basic requirement

The report should lead with TT100K traffic-sign detection. High-level situation analysis can remain a short optional extension only after the basic experiment is stable.

Rationale: the user explicitly wants to finish the basic content first, and the basic requirement has a concrete class-count risk.

Alternative considered: continue improving the workbench in parallel. This is deferred because it does not solve the current grading risk.

## Risks / Trade-offs

- Class names from TT100K raw categories may be less intuitive than the current manually named subset -> Mitigate by adding a clear class mapping table in the report.
- Rebuilt 10+ class training may produce lower mAP than the current 8-effective-class experiment -> Mitigate by presenting the task as more compliant and harder, and by using failure analysis to explain class imbalance and small-target difficulty.
- Full training may take significant GPU time -> Mitigate by using a staged plan: quick dataset/statistics validation first, then a stable YOLO11n run, then optional longer training if time remains.
- Old report figures may remain in the figure directory and be accidentally referenced -> Mitigate by naming final assets with a distinct compliant-experiment prefix and checking LaTeX references before final PDF export.
- Some selected high-frequency raw categories may not map cleanly to human-readable Chinese traffic-sign names -> Mitigate by documenting both TT100K source category code and normalized target name.

## Migration Plan

1. Compute raw TT100K category frequencies and choose a 10+ class subset with adequate sample counts.
2. Update class mapping and regenerate the YOLO-format dataset.
3. Verify class counts in train/val/test labels and save the statistics for the report.
4. Run a final YOLO11n training/validation experiment on the compliant dataset.
5. Export final assets and update the LaTeX report.
6. Compile the final PDF and inspect it for placeholder text, stale metrics, and mismatched figures.

Rollback is straightforward: the existing experiment folders and report assets remain available as historical references. If the new class subset performs poorly, choose a different high-frequency subset and repeat the dataset regeneration step before retraining.

## Open Questions

- What exact student names, IDs, class, and supervisor should replace the report placeholders?
- Should the final class subset use exactly 10 classes for faster training, or 12 classes to provide a buffer above the requirement?
- How much GPU time is available for the final run: a fast 20-epoch compliance run, or a stronger 50-epoch final run?
