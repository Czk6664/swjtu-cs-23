# 100 分冲刺增量包说明

本补丁用于在现有课程设计项目上追加两类最终冲刺实验：自集成推理和 IDB-IMDN-Lite 结构复现。补丁不包含 DIV2K 原始数据，也不包含 Conda 环境。

## 放置方式

将补丁包解压到原 `sr_course_design` 项目根目录并覆盖同名文件。

## 推荐运行顺序

先检查环境和模型结构：

```powershell
.\run_100pt_sprint_windows.ps1 -Stage smoke -Python "你的Python路径"
```

如果已经有 `checkpoints/imdn_no_edge_50ep_x2_best_psnr.ckpt`，运行自集成推理：

```powershell
.\run_100pt_sprint_windows.ps1 -Stage self-ensemble -Python "你的Python路径" -BestCheckpoint ".\checkpoints\imdn_no_edge_50ep_x2_best_psnr.ckpt"
```

如果时间充足，运行 IDB-IMDN-Lite 20 epoch：

```powershell
.\run_100pt_sprint_windows.ps1 -Stage idb-20 -Python "你的Python路径"
```

生成图表和报告：

```powershell
.\run_100pt_sprint_windows.ps1 -Stage assets -Python "你的Python路径"
.\run_100pt_sprint_windows.ps1 -Stage report -Python "你的Python路径"
```

## 需要带回的结果

- `results_100pt/`
- `logs/idb_imdn_x2_20ep_metrics.csv`
- `checkpoints/idb_imdn_20ep_x2.ckpt`
- `checkpoints/idb_imdn_20ep_x2_best_psnr.ckpt`
- `report/main_report.pdf`
- 若 Windows PDF 阅读器占用 `report/main_report.pdf`，请关闭阅读器后重新运行报告阶段；增量包会同时保留 `report/main_report_100pt.pdf` 作为同源编译出的备用 PDF。

如果没有 50 epoch checkpoint，本补丁仍可运行 smoke 和 IDB-IMDN-Lite 实验；自集成推理会明确报出缺少 checkpoint，而不会生成伪结果。
