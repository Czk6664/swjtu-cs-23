# sr_course_design

所属课程：[视觉计算](../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [ca-imdn-improvement-video/](ca-imdn-improvement-video/README.md)
- [checkpoints/](checkpoints/README.md)
- [imdn-process-video/](imdn-process-video/README.md)
- [logs/](logs/README.md)
- [openspec/](openspec/README.md)
- [report/](report/README.md)
- [src/](src/README.md)
- [tests/](tests/README.md)
- [tools/](tools/README.md)
- [CHECKLIST_100PT.md](CHECKLIST_100PT.md)
- [CHECKLIST_10PT.md](CHECKLIST_10PT.md)
- [CHECKLIST_CA_IMDN.md](CHECKLIST_CA_IMDN.md)
- [environment.yml](environment.yml)
- [EXPERIMENTS_10PT.md](EXPERIMENTS_10PT.md)
- [EXPERIMENTS_CA_IMDN.md](EXPERIMENTS_CA_IMDN.md)
- [literature_review.md](literature_review.md)
- [NEXT_EXPERIMENTS_INSTALL.md](NEXT_EXPERIMENTS_INSTALL.md)
- [PACKAGED_USAGE.md](PACKAGED_USAGE.md)
- [PATCH_INSTALL.md](PATCH_INSTALL.md)
- [project_plan.md](project_plan.md)
- [README_100PT_SPRINT.md](README_100PT_SPRINT.md)
- [README_10PT_EXPERIMENTS.md](README_10PT_EXPERIMENTS.md)
- [README_CA_IMDN_PATCH.md](README_CA_IMDN_PATCH.md)
- [report_outline.md](report_outline.md)
- [requirements-full.txt](requirements-full.txt)
- [requirements.txt](requirements.txt)
- [run_100pt_sprint_windows.ps1](run_100pt_sprint_windows.ps1)
- [run_10pt_experiments_windows.ps1](run_10pt_experiments_windows.ps1)
- [run_all_windows.ps1](run_all_windows.ps1)
- [run_ca_experiments_windows.ps1](run_ca_experiments_windows.ps1)
- [run_long_training_windows.ps1](run_long_training_windows.ps1)
- [run_next_experiments_windows.ps1](run_next_experiments_windows.ps1)
- [run_smoke_windows.ps1](run_smoke_windows.ps1)
- [setup_windows.ps1](setup_windows.ps1)

[返回上级目录](../README.md)

## 原有项目说明

"""Project usage notes for super-resolution course design."""

# 基于生成模型的图像超分辨率方法研究与轻量化改进设计

## 目录说明
- `project_plan.md`：课设总方案
- `report_outline.md`：报告大纲草稿
- `literature_review.md`：文献综述结构
- `src/models/`：MindSpore 模型实现
- `src/losses/`：损失函数
- `src/datasets/`：数据处理工具
- `src/train.py`：最小可运行训练入口，支持训练/验证集评估与每轮 CSV 记录
- `src/eval.py`：PSNR / SSIM 评估脚本
- `src/infer.py`：真实图像推理脚本，支持 Bicubic / SRCNN / IMDN 和 checkpoint 加载
- `src/smoke_test_ms.py`：MindSpore 前向冒烟测试
- `src/configs/`：SRCNN / IMDN / Edge Loss / Laplacian Loss 配置
- `tests/`：基础 smoke tests

## 当前状态
当前代码已经补成“CPU 可运行的最小闭环”，包含：
1. MindSpore 版 SRCNN 与 IMDN 模型
2. CombinedLoss / EdgeLoss / LaplacianLoss 作为 IMDN 结构损失消融入口
3. 真实图像读取、保存与 LR/HR 配对工具
4. 真实推理、真实评估、最小训练循环
5. 训练阶段支持训练集/验证集分离、每轮指标 CSV 记录
6. 基础 smoke tests

当前仍保留的限制：
- 不自动下载数据集
- 默认不附带训练好的 checkpoint
- 需要用户自行准备 `LR/` 与 `HR/` 目录下的成对图像

## 数据目录约定
训练或评估目录默认采用：

```text
<data_root>/
├── LR/
│   ├── 0001.png
│   └── ...
└── HR/
    ├── 0001.png
    └── ...
```

要求：
- LR 与 HR 文件名一一对应
- HR 尺寸应等于 `LR 尺寸 × scale`

## 示例命令
### 1. 冒烟前向验证
```bash
python src/smoke_test_ms.py
```

### 2. Bicubic 推理
```bash
python src/infer.py --model bicubic --scale 2 --input ./data/LR --output ./results/bicubic_x2
```

### 3. IMDN 推理
```bash
python src/infer.py --model imdn --scale 2 --num-features 32 --input ./data/LR --output ./results/imdn_x2
```

### 4. 评估结果
```bash
python src/eval.py --results ./results/imdn_x2 --targets ./data/HR --scale 2 --csv ./results/imdn_x2_metrics.csv
```

### 5. 最小训练
```bash
python src/train.py
```

或指定配置：
```bash
python src/train.py src/configs/srcnn_x2.yaml
python src/train.py src/configs/imdn_x2.yaml
python src/train.py src/configs/imdn_x2_edge.yaml
```

### 6. 公平快速对照与边缘权重消融
这些配置不会覆盖原有完整实验输出，适合在 CPU 上快速检查多 patch 采样、edge loss 权重和 Laplacian 结构损失影响：

```bash
python -m src.train src/configs/srcnn_x2_fair_quick.yaml
python -m src.train src/configs/imdn_x2_no_edge_fair_quick.yaml
python -m src.train src/configs/imdn_x2_edge_w001_quick.yaml
python -m src.train src/configs/imdn_x2_edge_w002_quick.yaml
python -m src.train src/configs/imdn_x2_laplacian_quick.yaml
```

新增训练配置字段：
- `patches_per_image`：每张 LR/HR 图像生成的随机 patch 数，默认 1。
- `edge_weight`：边缘损失权重，默认 0.05。
- `max_train_pairs` / `max_val_pairs`：用于快速实验的样本对上限，默认不限制。

### 7. 标准 benchmark 兼容评估
项目不自动下载 Set5 / Set14 / BSD100 / Urban100，但只要本地数据满足 `LR/` 和 `HR/` 成对目录格式，就可以运行：

```bash
python tools/run_benchmark_eval.py --benchmark-root ./data/Set5 --name Set5 --model bicubic --scale 2
python tools/run_benchmark_eval.py --benchmark-root ./data/Set5 --name Set5 --model imdn --scale 2 --num-features 32 --checkpoint ./checkpoints/imdn_no_edge_x2.ckpt
```

### 8. 图表再生成
```bash
python tools/generate_report_assets.py
```

该脚本从 CSV 指标文件生成训练曲线、总体指标柱状图、边缘权重消融图，以及正向/负向视觉对比图。

训练时会自动：
- 从 `dataset_dir` 读取训练集
- 从 `eval_dir` 读取验证集
- 每轮输出训练集的 `loss / PSNR / SSIM`
- 每轮输出验证集的 `PSNR / SSIM`
- 将每轮结果写入 `log_csv_path`

## 说明
本课程设计重点研究近年来生成模型在图像超分辨率中的应用思路，并以轻量重建模型作为实现主体，结合生成模型中的感知增强思想设计改进方案。当前实现优先保证“能在 CPU 上完成最小复现闭环”，后续可在接入 Set5 / Set14 / DIV2K 子集后继续补充正式实验结果。

## CPU 友好的分阶段学习率策略
当前训练脚本保持简单的固定学习率 Adam，以便在 MindSpore CPU 环境中稳定复现。若继续做长训实验，建议采用分阶段配置而不是一次性复杂 scheduler：

1. 阶段 1：`learning_rate: 0.0002`，训练到验证 PSNR 进入平台期。
2. 阶段 2：从上一阶段 checkpoint 继续，`learning_rate: 0.0001`。
3. 阶段 3：如仍有提升空间，降到 `learning_rate: 0.00005` 做收敛微调。

这样做的优点是实现成本低、日志清晰，也方便在报告中解释每个阶段的收益。
## DIV2K References
- Agustsson, Eirikur and Timofte, Radu. "NTIRE 2017 Challenge on Single Image Super-Resolution: Dataset and Study." CVPR Workshops, 2017.
- Timofte, Radu and others. "NTIRE 2017 Challenge on Single Image Super-Resolution: Methods and Results." CVPR Workshops, 2017.

## Data Access
- DIV2K official download page: https://data.vision.ee.ethz.ch/cvl/DIV2K/
- For the current `x2` setup in this repository, use HR `Train Data` and `Validation Data`.
- Use LR `NTIRE 2017 Track 1 bicubic downscaling x2` train/validation splits.

