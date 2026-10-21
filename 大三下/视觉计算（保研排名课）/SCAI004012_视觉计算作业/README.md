# SCAI004012_视觉计算作业

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

