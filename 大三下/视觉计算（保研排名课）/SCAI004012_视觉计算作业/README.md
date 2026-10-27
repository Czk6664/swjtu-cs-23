# SCAI004012_视觉计算作业

<!-- directory-guide:start -->
## 本层内容介绍

这里是“视觉计算”课程下的“SCAI004012_视觉计算作业”目录，主要用于整理该项课程实践的相关材料，具体内容见下方文件与子目录。

**阅读建议：**先读任务或报告了解目标，再看代码、数据和结果；借鉴方法后独立完成自己的任务。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **123 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

| 子目录 | 内容与用途 |
| --- | --- |
| [data](data/README.md) | 项目使用的数据或样例输入 |
| [report](report/README.md) | 报告文档或报告排版源文件 |
| [src](src/README.md) | 程序源代码与实现文件 |
| [tests](tests/README.md) | 测试代码、测试用例或测试输入 |
| [课程设计模版_视觉计算2026年](%E8%AF%BE%E7%A8%8B%E8%AE%BE%E8%AE%A1%E6%A8%A1%E7%89%88_%E8%A7%86%E8%A7%89%E8%AE%A1%E7%AE%972026%E5%B9%B4/README.md) | 课程文档或报告的模板及配套文件 |

- **文档与说明（1 份）**：[requirements.txt](requirements.txt)。

<!-- directory-guide:end -->

所属课程：[视觉计算](../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [data/](data/README.md)
- [report/](report/README.md)
- [src/](src/README.md)
- [tests/](tests/README.md)
- [课程设计模版_视觉计算2026年/](%E8%AF%BE%E7%A8%8B%E8%AE%BE%E8%AE%A1%E6%A8%A1%E7%89%88_%E8%A7%86%E8%A7%89%E8%AE%A1%E7%AE%972026%E5%B9%B4/README.md)
- [requirements.txt](requirements.txt)

[返回上级目录](../README.md)

## 原有项目说明

# SCAI004012《视觉计算》作业

本文件夹完成作业要求的图像直方图均衡、空间滤波、锐化滤波和基于傅里叶变换的频域滤波实验。

## 目录

- `src/`: Python 实现代码。
- `tests/`: 基础单元测试。
- `data/raw/`: 实验原始图像，由脚本生成，可复现。
- `data/processed/`: 各类滤波结果和中间频谱图。
- `report/figures/`: 实验对比图备份。
- `课程设计模版_视觉计算2026年/`: 按要求复制的 LaTeX 模板，已修改 `main_report.tex` 并复制实验图到 `figures/`。

## 运行

```bash
pip install -r requirements.txt
python src/run_experiments.py
pytest
cd 课程设计模版_视觉计算2026年
xelatex main_report.tex
xelatex main_report.tex
```

提交前请把 `课程设计模版_视觉计算2026年/main_report.tex` 封面中的专业、学号、姓名等占位信息替换为真实信息。

