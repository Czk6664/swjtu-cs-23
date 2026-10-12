## 1. Class Selection And Dataset Audit

- [x] 1.1 Scan raw `annotations_all.json` and produce candidate TT100K category frequencies sorted by object count.
- [x] 1.2 Select a final 10-12 class subset where every class has enough raw samples for train/validation/test evaluation.
- [x] 1.3 Define normalized class names and a source-code-to-report-name mapping for the selected TT100K categories.
- [x] 1.4 Verify the selected subset excludes the current zero-sample configured classes from final requirement counting.

## 2. YOLO Dataset Rebuild

- [x] 2.1 Update the TT100K class mapping used by the conversion pipeline.
- [x] 2.2 Regenerate `traffic_sign_detection/data/tt100k_yolo` from the raw TT100K dataset.
- [x] 2.3 Regenerate `traffic_sign_detection/configs/dataset/tt100k.yaml` so it matches the final class subset.
- [x] 2.4 Produce train/validation/test image counts, label-file counts, and per-class object counts for the rebuilt dataset.
- [x] 2.5 Confirm at least 10 class IDs have nonzero labels after conversion.

## 3. Final YOLO11n Experiment

- [x] 3.1 Create or update the final YOLO11n experiment config for the compliant TT100K subset.
- [x] 3.2 Run a validation smoke test to confirm the rebuilt dataset loads correctly.
- [ ] 3.3 Train YOLO11n on the compliant subset with the chosen stable settings.
- [ ] 3.4 Validate the best checkpoint and record Precision, Recall, mAP50, and mAP50-95.
- [ ] 3.5 Save final weights, `results.csv`, training curves, confusion matrices, and validation prediction examples under a clearly named final experiment directory.

## 4. Report Asset Export

- [ ] 4.1 Export or copy final experiment figures into `课程设计模版_2026年/figures/tt100k_experiment` with names that distinguish them from historical 8-effective-class runs.
- [x] 4.2 Generate a dataset statistics table suitable for inclusion in the LaTeX report.
- [ ] 4.3 Generate an experiment results table that references only the final compliant run as main evidence.

## 5. Report Update

- [ ] 5.1 Update the dataset section to describe the final 10+ effective class subset and include the source category mapping.
- [ ] 5.2 Update implementation details to reference the final dataset config, experiment config, and training settings.
- [ ] 5.3 Update quantitative experiment tables with final metrics from the compliant run.
- [ ] 5.4 Update qualitative figures, confusion matrix discussion, and failure-case analysis to match the final experiment assets.
- [ ] 5.5 Update problem analysis and improvement ideas to reflect the harder 10+ class task, including class imbalance and small-target issues.
- [ ] 5.6 Replace report placeholders for student ID, names, class, and supervisor.

## 6. Verification And Handoff

- [ ] 6.1 Search the LaTeX source for stale placeholder text and old metric values.
- [ ] 6.2 Compile the final report PDF successfully.
- [ ] 6.3 Inspect the compiled PDF for missing figures, inconsistent class counts, and stale experiment references.
- [ ] 6.4 Run a final checklist comparing the completed work against all basic assignment requirements.
- [ ] 6.5 Record the final run path, final weights path, final PDF path, and any remaining limitations for handoff.
