# workbench

<!-- directory-guide:start -->
## 本层内容介绍

这里是“智能+交通”课程下的“workbench”目录，主要用于整理此模块的源码及配套文件。

**阅读建议：**从上级项目说明确认模块职责，再结合文件名查找实现；具体入口和运行方法以源码及原说明为准。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **42 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

| 子目录 | 内容与用途 |
| --- | --- |
| [runtime](runtime/README.md) | 该主题的配套文件或下级模块 |

- **代码与脚本（5 份）**：[app.js](app.js)、[index.html](index.html)等；完整列表见本页导航。

<!-- directory-guide:end -->

所属课程：[智能+交通](../../../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [runtime/](runtime/README.md)
- [app.js](app.js)
- [index.html](index.html)
- [start.bat](start.bat)
- [start_workbench.bat](start_workbench.bat)
- [styles.css](styles.css)

[返回上级目录](../README.md)

## 原有项目说明

# 交通态势工作台运行说明

## 1. 启动方式

在项目根目录执行：

```powershell
cd D:\大三下\智能交通\大作业2\solution_design\workbench
python server.py
```

终端出现 `http://127.0.0.1:8765` 后，在浏览器打开该地址即可。

## 2. 页面现在能做什么

- 调用 `YOLO11n` 权重 `exp_B_704_b8_w02\weights\best.pt`，对上传图片或 TT100K 样例图执行交通标志识别
- 读取 `D:\大三下\智能交通\大作业1\results` 下的 STAEformer 结果文件，展示交通流预测指标
- 将识别结果与预测趋势融合成一段交通态势分析文字

## 3. 演示建议

1. 先点击“运行识别”，展示检测框和类别摘要
2. 再点击“运行预测”，展示 MAE、RMSE、MAPE 和步长结果
3. 最后切到“交通态势研判”，说明系统如何把道路规则语义和未来流量趋势结合起来

## 4. 运行依赖

- 当前 Python 环境需要已安装 `ultralytics`
- 页面默认使用本地已有实验资产，不依赖联网下载模型

