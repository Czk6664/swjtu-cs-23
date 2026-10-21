# 报告大纲草稿

## 1 团队成员分工
- 成员A：负责文献检索、相关工作整理、理论分析。
- 成员B：负责模型实现、实验设计与结果整理。
- 成员C：负责改进方法设计、图表制作与 LaTeX 排版。

## 2 任务背景
图像超分辨率旨在从低分辨率图像中恢复高分辨率细节，在医学图像、视频增强、遥感成像和老照片修复等场景中具有重要应用价值。近年来，随着深度学习技术的发展，超分辨率方法从传统插值和卷积神经网络逐步发展到生成对抗网络和扩散模型，在感知质量与重建精度方面均取得了明显进展。

## 3 任务描述
本课程设计聚焦单图像超分辨率任务，围绕“生成模型的图像超分辨率方法”展开研究。通过查阅近五年代表性论文，分析生成式超分方法的核心思想与技术演化；在实验部分，以 MindSpore 实现轻量超分模型作为主线，并结合生成模型思想设计改进方案，完成定量与定性分析。

## 4 技术方案
### 4.1 方案总体架构
整体方案分为文献研究、模型实现、改进设计和实验评估四个部分。首先综述轻量重建模型、GAN 超分模型和扩散超分模型的发展脉络；然后基于 MindSpore 搭建基线模型；再在基线模型上引入轻量改进模块；最后通过公开数据集对模型效果进行评估。

### 4.2 文献研究模块
建议重点分析以下三类方法：
1. 轻量重建模型：IMDN / RFDN / ESRT
2. GAN 超分模型：Real-ESRGAN
3. 扩散超分模型：SR3 / StableSR

### 4.3 模型实现模块
- 基线模型：SRCNN
- 主模型：IMDN
- 改进模型：IMDN + Edge Loss 或 IMDN + Attention

### 4.4 改进设计模块
从生成式超分辨率方法中借鉴“感知质量增强”的思想，在轻量模型中加入边缘损失、感知损失或轻量注意力模块，使模型在保证重建精度的同时获得更好的视觉恢复效果。

## 5 实验
### 5.1 数据集
可选用 Set5、Set14、BSD100 或 DIV2K 子集作为实验数据。训练阶段可采用双三次下采样生成低分辨率样本。

### 5.2 评测指标
- PSNR
- SSIM
- 视觉对比图

### 5.3 实现细节
- 深度学习框架：MindSpore
- 训练设备：CPU 可跑的最小实验流程，正式训练可切换到 GPU
- 放大倍率：x2 或 x4
- 损失函数：L1 / L2 + Edge Loss（可选）
- 优化器：Adam
- 训练日志：每轮保存训练/验证指标到 CSV
- 验证流程：从 `eval_dir` 读取独立验证集，按 epoch 统计 PSNR / SSIM

### 5.4 定量实验
1. 与其他方法比较：比较 SRCNN、IMDN 和改进模型的 PSNR/SSIM
2. 消融实验：分析边缘损失或注意力模块的作用
3. 超参数分析：分析学习率、损失权重等参数的影响
4. 训练曲线记录：结合 CSV 日志展示每轮 loss / PSNR / SSIM 变化

### 5.5 定性实验
1. 案例分析：展示纹理、边缘和细节恢复效果
2. 特征可视化分析：对部分特征图或输出结果进行可视化展示

## 6 总结
总结本文对生成模型超分辨率方法的研究结论，说明轻量模型的可复现性和改进方案的有效性，并分析后续可进一步研究的方向，例如真实退化建模和更高效的生成式超分框架。

## 7 实验记录说明
- 训练脚本会将每轮指标写入 `log_csv_path`
- 验证集单独放在 `eval_dir`
- 报告中可直接引用 CSV 中的 loss / PSNR / SSIM 曲线和最终验证结果
## DIV2K Dataset Note
- If the experiments use DIV2K, cite the dataset paper: Agustsson and Timofte, "NTIRE 2017 Challenge on Single Image Super-Resolution: Dataset and Study," CVPR Workshops, 2017.
- Also cite one challenge report. Recommended: Timofte and others, "NTIRE 2017 Challenge on Single Image Super-Resolution: Methods and Results," CVPR Workshops, 2017.
- Data access: https://data.vision.ee.ethz.ch/cvl/DIV2K/
- For the current course project implementation, use the HR train/validation splits and the NTIRE 2017 Track 1 bicubic x2 LR splits.
