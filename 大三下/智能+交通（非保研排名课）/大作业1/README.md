# 大作业1

所属课程：[智能+交通](../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [document-format-skills-main/](document-format-skills-main/README.md)
- [figures/](figures/README.md)
- [improvements/](improvements/README.md)
- [results/](results/README.md)
- [zeroai-main/](zeroai-main/README.md)
- [.$Fig_LA_STAEformer_Architecture.xml.bkp](.%24Fig_LA_STAEformer_Architecture.xml.bkp)
- [2308.10425v5.pdf](2308.10425v5.pdf)
- [2308.10425v5_translated.pdf](2308.10425v5_translated.pdf)
- [analyze_staeformer.py](analyze_staeformer.py)
- [create_staeformer_tex.py](create_staeformer_tex.py)
- [data_prepare.py](data_prepare.py)
- [Fig_DGL_STAEformer_Architecture.xml](Fig_DGL_STAEformer_Architecture.xml)
- [Fig_LA_STAEformer_Architecture.xml](Fig_LA_STAEformer_Architecture.xml)
- [Fig_MST_STAEformer_Architecture.xml](Fig_MST_STAEformer_Architecture.xml)
- [generate_embedding_pdf.py](generate_embedding_pdf.py)
- [generate_embedding_ppt.py](generate_embedding_ppt.py)
- [generate_staeformer_complete_excel.py](generate_staeformer_complete_excel.py)
- [install_requirements.bat](install_requirements.bat)
- [metrics.py](metrics.py)
- [plot_embedding_layers.py](plot_embedding_layers.py)
- [requirements.txt](requirements.txt)
- [setup_environment.bat](setup_environment.bat)
- [STAEformer.py](STAEformer.py)
- [STAEformer.yaml](STAEformer.yaml)
- [STAEformer_academic.pdf](STAEformer_academic.pdf)
- [STAEformer_v2.pdf](STAEformer_v2.pdf)
- [STAEformer_嵌入层介绍.pptx](STAEformer_%E5%B5%8C%E5%85%A5%E5%B1%82%E4%BB%8B%E7%BB%8D.pptx)
- [STAEformer_嵌入层详解.pdf](STAEformer_%E5%B5%8C%E5%85%A5%E5%B1%82%E8%AF%A6%E8%A7%A3.pdf)
- [STAEformer_嵌入层详解.png](STAEformer_%E5%B5%8C%E5%85%A5%E5%B1%82%E8%AF%A6%E8%A7%A3.png)
- [Steaformer_Excel_Style.tex](Steaformer_Excel_Style.tex)
- [train.py](train.py)
- [utils.py](utils.py)
- [大作业1_STAEformer.docx](%E5%A4%A7%E4%BD%9C%E4%B8%9A1_STAEformer.docx)
- [实验报告_STAEformer_分析.md](%E5%AE%9E%E9%AA%8C%E6%8A%A5%E5%91%8A_STAEformer_%E5%88%86%E6%9E%90.md)
- [智能交通程泽凯组.pptx](%E6%99%BA%E8%83%BD%E4%BA%A4%E9%80%9A%E7%A8%8B%E6%B3%BD%E5%87%AF%E7%BB%84.pptx)

[返回上级目录](../README.md)

## 原有项目说明

## STAEformer: Spatio-Temporal Adaptive Embedding Transformer

#### H. Liu*, Z. Dong*, R. Jiang#, J. Deng, J. Deng, Q. Chen, X. Song#, "Spatio-Temporal Adaptive Embedding Makes Vanilla Transformer SOTA for Traffic Forecasting", Proc. of 32nd ACM International Conference on Information and Knowledge Management (CIKM), 2023. (*Equal Contribution, #Corresponding Author)

![model_arch](https://github.com/XDZhelheim/STAEformer/assets/57553691/f0620d5b-2b7f-47bc-bf76-5fccf48fae35)

#### Citation
```
@inproceedings{liu2023spatio,
  title={Spatio-temporal adaptive embedding makes vanilla transformer sota for traffic forecasting},
  author={Liu, Hangchen and Dong, Zheng and Jiang, Renhe and Deng, Jiewen and Deng, Jinliang and Chen, Quanjun and Song, Xuan},
  booktitle={Proceedings of the 32nd ACM International Conference on Information and Knowledge Management},
  pages={4125--4129},
  year={2023}
}
```

#### CIKM23 Proceedings (including METRLA, PEMSBAY, PEMS04, PEMS07, PEMS08 results)
[https://dl.acm.org/doi/abs/10.1145/3583780.3615160](https://dl.acm.org/doi/10.1145/3583780.3615160)

#### Preprints (including METRLA, PEMSBAY, PEMS03, PEMS04, PEMS07, PEMS08 results)
[![Arxiv link](https://img.shields.io/static/v1?label=arXiv&message=STAEformer&color=red&logo=arxiv)](https://arxiv.org/abs/2308.10425)

#### Performance on Traffic Forecasting Benchmarks

![perf1](https://github.com/XDZhelheim/STAEformer/assets/57553691/8049bce2-9bc2-4248-a911-25468e9bbab4)

<img width="600" alt="image" src="https://github.com/XDZhelheim/STAEformer/assets/57553691/abf009aa-b145-451c-aff6-27031d60a612">

#### Required Packages

```
pytorch>=1.11
numpy
pandas
matplotlib
pyyaml
pickle
torchinfo
```

#### Training Commands

```bash
cd model/
python train.py -d <dataset> -g <gpu_id>
```

`<dataset>`:
- METRLA
- PEMSBAY
- PEMS03
- PEMS04
- PEMS07
- PEMS08

