from pyspark.sql import SparkSession


def main() -> None:
    spark = SparkSession.builder.appName("CourseProjectWordCount").getOrCreate()
    sc = spark.sparkContext

    input_path = "file:///opt/spark/work/data/sample.txt"
    lines = sc.textFile(input_path)
    word_counts = (
        lines.flatMap(lambda line: line.split())
        .map(lambda word: (word.strip().lower(), 1))
        .filter(lambda item: item[0])
        .reduceByKey(lambda a, b: a + b)
        .sortBy(lambda item: item[1], ascending=False)
    )

    print("Top 10 words:", word_counts.take(10))
    spark.stop()


if __name__ == "__main__":
    main()
