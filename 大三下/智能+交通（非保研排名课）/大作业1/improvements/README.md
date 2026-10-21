# improvements

所属课程：[智能+交通](../../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [00_Baseline/](00_Baseline/README.md)
- [01_External_Feature_Fusion/](01_External_Feature_Fusion/README.md)
- [02_Dynamic_Graph_Learning/](02_Dynamic_Graph_Learning/README.md)
- [03_Lightweight_Attention/](03_Lightweight_Attention/README.md)
- [04_Multi_Scale_Time/](04_Multi_Scale_Time/README.md)
- [lib/](lib/README.md)
- [models/](models/README.md)
- [generate_plots.py](generate_plots.py)
- [generate_plots_all.py](generate_plots_all.py)
- [run_all.py](run_all.py)
- [run_all_models.bat](run_all_models.bat)
- [run_all_models_all_datasets.bat](run_all_models_all_datasets.bat)
- [train.py](train.py)
- [train_baseline.py](train_baseline.py)
- [training_output.txt](training_output.txt)
- [第七章_改进模型实验结果与对比分析.md](%E7%AC%AC%E4%B8%83%E7%AB%A0_%E6%94%B9%E8%BF%9B%E6%A8%A1%E5%9E%8B%E5%AE%9E%E9%AA%8C%E7%BB%93%E6%9E%9C%E4%B8%8E%E5%AF%B9%E6%AF%94%E5%88%86%E6%9E%90.md)

[返回上级目录](../README.md)

## 原有项目说明

# STAEformer 改进模型实验

本目录包含基于STAEformer交通流预测模型的四种改进方案实现，以及完整的基线模型对比实验。

## 目录结构

```
improvements/
├── 00_Baseline/                    # STAEformer 基线模型
│   └── run.bat
├── 01_External_Feature_Fusion/    # 改进方案1：外部特征融合 (EFF)
│   ├── model.py
│   └── run.bat
├── 02_Dynamic_Graph_Learning/     # 改进方案2：动态图学习 (DGL)
│   ├── model.py
│   └── run.bat
├── 03_Lightweight_Attention/      # 改进方案3：轻量化注意力 (LA)
│   ├── model.py
│   └── run.bat
├── 04_Multi_Scale_Time/           # 改进方案4：多尺度时间建模 (MST)
│   ├── model.py
│   └── run.bat
├── lib/                           # 公共库
│   ├── utils.py
│   ├── metrics.py
│   └── data_prepare.py
├── models/                        # 基础模型
│   └── base_staeformer.py
├── results/                       # 实验结果（自动生成）
├── train.py                       # 改进模型训练脚本
├── train_baseline.py              # 基线模型训练脚本
├── generate_plots.py              # 生成对比图表（单数据集）
├── generate_plots_all.py          # 生成对比图表（所有数据集）
├── run_all_models.bat             # 运行所有模型（单数据集）
├── run_all_models_all_datasets.bat # 运行所有模型（所有数据集）
└── 第七章_改进模型实验结果与对比分析.md
```

## 改进方案说明

### 1. 外部特征融合 (EFF)
在模型输入端引入天气、节假日、道路事件等外部特征，提高模型对异常场景的适应性。

### 2. 动态图学习 (DGL)
结合动态图结构学习方法，实时挖掘交通网络中的潜在空间依赖关系。

### 3. 轻量化注意力 (LA)
将稠密注意力替换为稀疏/线性注意力，复杂度从O(N²)降低到O(N)，适用于大规模路网。

### 4. 多尺度时间建模 (MST)
设计分层时间编码模块，分别提取短期、日周期、周周期等不同尺度的时间特征。

## 快速开始

### 环境配置
```bash
pip install torch numpy pandas pyyaml torchinfo matplotlib
```

### 运行所有模型（单数据集）
```bash
cd improvements
run_all_models.bat
```

### 运行所有模型（所有数据集）
```bash
cd improvements
run_all_models_all_datasets.bat
```

### 单独运行某个模型
```bash
cd improvements/00_Baseline
run.bat
```

## 命令行参数

### train_baseline.py
```bash
python train_baseline.py --dataset PEMS08 --epochs 200 --batch_size 16 --lr 0.001
```

### train.py
```bash
python train.py --model eff --dataset PEMS08 --epochs 200 --batch_size 16 --lr 0.001
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --model | 模型类型 (eff/dgl/la/mst) | 必填 |
| --dataset | 数据集名称 | PEMS08 |
| --epochs | 最大训练轮数 | 200 |
| --batch_size | 批大小 | 16 |
| --lr | 学习率 | 0.001 |
| --early_stop | 早停耐心值 | 30 |
| --output_dir | 结果输出目录 | results/ |

## 数据集

支持的数据集：
- **PEMS08** (170节点) - 加州高速公路
- **PEMS04** (307节点) - 加州高速公路
- **PEMS07** (883节点) - 加州高速公路
- **METRLA** (207节点) - 洛杉矶高速公路
- **PEMSBAY** (325节点) - 旧金山湾区

数据格式：
```
data/
├── PEMS08/
│   ├── data.npz    # (T, N, C) 交通数据
│   └── index.npz   # 训练/验证/测试索引
```

## 结果文件

实验结果保存在 `results/` 目录：

| 文件 | 说明 |
|------|------|
| `baseline_*.json` | 基线模型详细结果 |
| `eff_*.json` | EFF模型详细结果 |
| `dgl_*.json` | DGL模型详细结果 |
| `la_*.json` | LA模型详细结果 |
| `mst_*.json` | MST模型详细结果 |
| `comparison_all_datasets.png` | 所有数据集MAE/RMSE/MAPE对比图 |
| `comparison_average.png` | 平均性能对比图 |
| `comparison_per_step.png` | 各时间步预测对比图 |
| `summary_all_results.txt` | 完整结果文本汇总 |

## 模型对比

| 模型 | 参数量 | 计算复杂度 | 精度 | 推理速度 |
|------|--------|------------|------|----------|
| Baseline | ~1.2M | O(N²×D) | 基准 | 慢 |
| EFF | ~1.3M | O(N²×D) | 待定 | 慢 |
| DGL | ~1.4M | O(N²×D) | 待定 | 慢 |
| LA | ~1.2M | O(N×D) | 待定 | 快 |
| MST | ~1.3M | O(N²×D) | 待定 | 慢 |

## 预期实验结果

运行完所有模型后，图表将自动显示：
1. 5个数据集 × 5个模型 = 25组实验结果
2. 每个数据集的MAE/RMSE/MAPE柱状图对比
3. 各模型平均性能对比
4. 12步预测中每步的性能曲线对比

