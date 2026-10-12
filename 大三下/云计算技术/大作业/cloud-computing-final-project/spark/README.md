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
