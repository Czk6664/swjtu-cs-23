# spark

<!-- directory-guide:start -->
## 本层内容介绍

这里是“云计算技术”课程下的“spark”目录，主要用于整理此模块的源码及配套文件。

**阅读建议：**从上级项目说明确认模块职责，再结合文件名查找实现；具体入口和运行方法以源码及原说明为准。

**项目背景与使用步骤：**请继续阅读本页下方的“原有项目说明”，其中保留了项目自己的功能介绍、环境要求或运行方法。

### 本层有哪些内容

本目录及子目录共收录 **26 份文件**（不含各层 README）；下面先介绍本层直接可见的内容。

| 子目录 | 内容与用途 |
| --- | --- |
| [data](data/README.md) | 项目使用的数据或样例输入 |

- **配置及其他配套文件（14 份）**：[Dockerfile.analysis-teacher](Dockerfile.analysis-teacher)、[Dockerfile.spark](Dockerfile.spark)等；完整列表见本页导航。
- **代码与脚本（5 份）**：[analysis.py](analysis.py)、[generate_douban_report_figures.py](generate_douban_report_figures.py)等；完整列表见本页导航。

<!-- directory-guide:end -->

所属课程：[云计算技术](../../../README.md)。

感谢 **Cheng Zekai** 提供或整理本目录资料。原作者与第三方项目署名以文件原文为准。

## 本层导航

- [data/](data/README.md)
- [analysis.py](analysis.py)
- [Dockerfile.analysis-teacher](Dockerfile.analysis-teacher)
- [Dockerfile.spark](Dockerfile.spark)
- [generate_douban_report_figures.py](generate_douban_report_figures.py)
- [pandas_douban_performance.py](pandas_douban_performance.py)
- [performance_compare.py](performance_compare.py)
- [spark-analysis-job.yaml](spark-analysis-job.yaml)
- [spark-operator-1.1.27.tgz](spark-operator-1.1.27.tgz)
- [spark-operator-2.1.1.tgz](spark-operator-2.1.1.tgz)
- [spark-operator-2.3.0.tgz](spark-operator-2.3.0.tgz)
- [spark-operator-2.5.0.tgz](spark-operator-2.5.0.tgz)
- [spark-operator-teacher-values.yaml](spark-operator-teacher-values.yaml)
- [sparkapplication-analysis-teacher.yaml](sparkapplication-analysis-teacher.yaml)
- [sparkapplication-douban-perf-1.yaml](sparkapplication-douban-perf-1.yaml)
- [sparkapplication-douban-perf-2.yaml](sparkapplication-douban-perf-2.yaml)
- [sparkapplication-wordcount-online.yaml](sparkapplication-wordcount-online.yaml)
- [sparkapplication-wordcount-teacher.yaml](sparkapplication-wordcount-teacher.yaml)
- [sparkapplication.yaml](sparkapplication.yaml)
- [wordcount.py](wordcount.py)

[返回上级目录](../README.md)

## 原有项目说明

# Spark 方向 A 大作业内容

本目录覆盖第二部分方向 A：Spark 大数据分析。正式运行时，将 `sparkapplication.yaml` 中的镜像和 OBS 路径替换为教师提供的值。

## 文件说明

- `sparkapplication.yaml`：Spark Operator 提交作业的 CR 配置。
- `wordcount.py`：入门验证作业，用于截图 Driver/Executor Pod。
- `analysis.py`：数据清洗、缺失值统计、SQL 分析和窗口/JOIN 查询。
- `performance_compare.py`：汇总 Pandas、PySpark 1 executor、PySpark 2 executor 的耗时并生成图表。
- `data/sample_movies.csv`：小样例数据，说明字段结构。
- `data/performance_timings.json`：性能记录样例，实际报告应替换为真实测试数据。

## 安装 Spark Operator

```bash
helm install spark-op ./spark-operator-chart/ -n spark-operator --create-namespace
```

## 提交验证作业

将 `wordcount.py` 放入教师提供的 PySpark 镜像，或使用课程给定镜像中的路径，然后提交作业：

```bash
kubectl apply -f sparkapplication.yaml
kubectl get pods -n default
kubectl logs <driver-pod-name>
```

截图要求：Driver Pod 和 Executor Pod 可见，Driver 完成后日志包含输出结果。

## 运行数据分析

`analysis.py` 支持一个输入参数：

```bash
spark-submit analysis.py s3a://<BUCKET>/douban_movies.csv
```

输出必须截图：

- Schema。
- 前 5 行。
- 各字段缺失比例。
- 清洗前后行数。
- GROUP BY、Top-N、时间趋势、窗口函数或 JOIN 查询结果。

## 性能对比

记录三种模式各 3 次耗时，填入 `data/performance_timings.json`：

- `pandas`
- `pyspark-1-executor`
- `pyspark-2-executors`

生成汇总：

```bash
python performance_compare.py --input data/performance_timings.json
```

报告中结合 Amdahl 定律说明：实际加速比低于线性加速，通常来自任务启动开销、Shuffle、序列化、网络通信和不可并行部分。

