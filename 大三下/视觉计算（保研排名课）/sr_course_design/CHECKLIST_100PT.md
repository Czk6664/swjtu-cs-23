# 100 分冲刺检查清单

- [ ] `pytest tests/test_models.py tests/test_self_ensemble.py -q` 通过。
- [ ] `checkpoints/idb_imdn_smoke_x2.ckpt` 存在。
- [ ] `results_100pt/idb_imdn_smoke_x2_eval_metrics.csv` 存在。
- [ ] 若运行正式自集成：`results_100pt/self_ensemble/*_self_ensemble_summary.csv` 存在。
- [ ] 若运行 IDB 20ep：`results_100pt/idb_imdn_20ep_x2_eval_metrics.csv` 存在。
- [ ] `results_100pt/summaries/model_comparison_100pt.csv` 存在。
- [ ] 若有自集成结果：`report/figures/self_ensemble_metrics.png` 和 `report/figures/self_ensemble_visual_grid.png` 非空。
- [ ] 若有 IDB 结果：`report/figures/idb_imdn_comparison.png` 非空。
- [ ] `report/main_report.pdf` 编译成功，无 LaTeX Error、undefined references、undefined citations；如果该文件被阅读器占用，检查同源备用文件 `report/main_report_100pt.pdf`。
- [ ] `dist/sr_100pt_sprint_patch.zip` 存在，且不包含 DIV2K 原始数据目录。
