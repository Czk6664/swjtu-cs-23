# CA-IMDN 补强检查清单

## 跑实验前

- `pytest tests/test_models.py -q` 通过。
- `pytest tests/test_infer_smoke.py -q` 通过。
- `data/eval/LR` 和 `data/eval/HR` 存在且包含 100 张验证图。
- MindSpore 环境可运行 `python -m src.smoke_test_ms`。

## 跑实验后

- 每个新增实验都应有 checkpoint：
  - `checkpoints/<model>_x2.ckpt`
- 每个新增实验都应有训练日志：
  - `logs/<experiment>_metrics.csv`
- 每个新增实验都应有 100 张推理图像：
  - `results/<model>_x2_eval/*.png`
- 每个新增实验都应有 100 行评估 CSV：
  - `results/<model>_x2_eval_metrics.csv`

## 报告前检查

- `results/summaries/experiment_summary.csv` 已生成。
- `results/summaries/parameter_counts.csv` 已生成。
- `report/figures/frequency_analysis.png` 非空。
- `xelatex` 编译两遍成功。
- `report/main_report.log` 不包含：
  - `LaTeX Error`
  - `undefined references`
  - `Emergency stop`
