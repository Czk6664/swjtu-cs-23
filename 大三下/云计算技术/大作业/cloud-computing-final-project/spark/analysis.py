import os
import sys
import time

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F


DEFAULT_INPUT = "data/douban_movies.csv"


def main() -> None:
    input_path = sys.argv[1] if len(sys.argv) > 1 else os.getenv("OBS_INPUT_PATH", DEFAULT_INPUT)
    spark = (
        SparkSession.builder.appName("CourseProjectDoubanAnalysis")
        .config("spark.sql.shuffle.partitions", os.getenv("SPARK_SQL_SHUFFLE_PARTITIONS", "8"))
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    print(f"===== OFFICIAL DATASET INPUT PATH: {input_path} =====")
    raw = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .option("multiLine", True)
        .option("quote", '"')
        .option("escape", '"')
        .csv(input_path)
    )

    print("===== OFFICIAL DATASET SCHEMA =====")
    raw.printSchema()
    print("===== OFFICIAL DATASET FIRST 5 ROWS =====")
    raw.select(
        "movie_id", "title", "year", "rating_score", "rating_count", "genres", "countries"
    ).show(5, truncate=35)

    total_rows = raw.count()
    print(f"===== RAW ROW COUNT: {total_rows} =====")
    print("===== MISSING VALUE RATIOS =====")
    missing_exprs = [
        F.sum(
            F.when(F.col(c).isNull() | (F.trim(F.col(c).cast("string")) == ""), 1).otherwise(0)
        ).alias(f"{c}_missing")
        for c in raw.columns
    ]
    missing_counts = raw.select(missing_exprs).first().asDict()
    for column in raw.columns:
        missing = int(missing_counts[f"{column}_missing"])
        ratio = missing / total_rows * 100
        print(f"{column:<16} missing={missing:>6} ratio={ratio:>6.2f}%")
    zero_rating_rows = raw.where(F.col("rating_score").cast("double") <= 0).count()
    print(f"===== ENCODED ZERO RATING ROW COUNT: {zero_rating_rows} =====")

    cleaned = clean_movies(raw).cache()
    cleaned_rows = cleaned.count()
    print(f"===== CLEANED ROW COUNT: {cleaned_rows} =====")
    print("===== REMOVED ROW COUNT: {} =====".format(total_rows - cleaned_rows))
    print("===== BASIC STATISTICS AFTER CLEANING =====")
    cleaned.select("rating", "year", "vote_count", "collect_count").summary(
        "mean", "stddev", "min", "max"
    ).show(truncate=False)

    run_queries(cleaned)
    run_timed_query(spark, input_path)
    cleaned.unpersist()
    spark.stop()


def clean_movies(df):
    prepared = (
        df.withColumn("rating", F.col("rating_score").cast("double"))
        .withColumn("vote_count", F.col("rating_count").cast("long"))
        .withColumn("collect_count", F.col("collect_count").cast("long"))
        .withColumn("year", F.col("year").cast("int"))
        .withColumn("genre", F.trim(F.col("genres")))
        .withColumn("country", F.trim(F.col("countries")))
    )

    # Null and zero scores both represent movies without an effective user rating.
    # They are excluded because rating is the core measurement of later comparisons.
    no_missing_rating = prepared.dropna(subset=["rating"]).where(F.col("rating") > 0)

    # Descriptive fields are filled to retain scored movies in grouping statistics.
    return no_missing_rating.fillna(
        {
            "genre": "未知类型",
            "country": "未知地区",
            "directors": "未知导演",
            "summary": "暂无简介",
        }
    )


def exploded_genres(df):
    return (
        df.withColumn("single_genre", F.explode(F.split(F.col("genre"), "/")))
        .withColumn("single_genre", F.trim(F.col("single_genre")))
        .where(F.col("single_genre") != "")
    )


def genre_aggregate(df):
    return (
        exploded_genres(df)
        .groupBy("single_genre")
        .agg(
            F.count("*").alias("movie_count"),
            F.round(F.avg("rating"), 2).alias("avg_rating"),
            F.sum("vote_count").alias("rating_votes"),
        )
        .orderBy(F.desc("movie_count"), F.desc("avg_rating"))
    )


def run_queries(df) -> None:
    print("===== QUERY 1: GROUP BY EXPLODED GENRE (TOP 15 BY MOVIE COUNT) =====")
    genre_aggregate(df).show(15, truncate=False)

    print("===== QUERY 2: ORDER BY TOP-N HIGH-RATED MOVIES (RATING_COUNT >= 100000) =====")
    (
        df.where(F.col("vote_count") >= 100000)
        .select("title", "year", "rating", "vote_count", "genre")
        .orderBy(F.desc("rating"), F.desc("vote_count"))
        .show(10, truncate=40)
    )

    print("===== QUERY 3: TIME TREND BY YEAR (2015-2024) =====")
    (
        df.where((F.col("year") >= 2015) & (F.col("year") <= 2024))
        .groupBy("year")
        .agg(F.count("*").alias("movie_count"), F.round(F.avg("rating"), 2).alias("avg_rating"))
        .orderBy("year")
        .show(20, truncate=False)
    )

    print("===== QUERY 4: WINDOW TOP-3 MOVIES IN FIVE MAJOR GENRES =====")
    genre_movies = exploded_genres(df).where(
        F.col("single_genre").isin("剧情", "喜剧", "动作", "爱情", "科幻")
    )
    ranking = Window.partitionBy("single_genre").orderBy(F.desc("rating"), F.desc("vote_count"))
    (
        genre_movies.withColumn("rank_in_genre", F.row_number().over(ranking))
        .where(F.col("rank_in_genre") <= 3)
        .select("single_genre", "rank_in_genre", "title", "year", "rating", "vote_count")
        .orderBy("single_genre", "rank_in_genre")
        .show(20, truncate=35)
    )

    print("===== QUERY 5: JOIN GENRE DIMENSION AND AGGREGATE =====")
    genre_dimension = SparkSession.getActiveSession().createDataFrame(
        [
            ("剧情", "叙事与情感"),
            ("爱情", "叙事与情感"),
            ("喜剧", "叙事与情感"),
            ("动作", "类型与商业"),
            ("科幻", "类型与商业"),
            ("悬疑", "类型与商业"),
            ("犯罪", "类型与商业"),
            ("动画", "动画与纪录"),
            ("纪录片", "动画与纪录"),
        ],
        ["single_genre", "genre_group"],
    )
    (
        exploded_genres(df)
        .join(F.broadcast(genre_dimension), on="single_genre", how="inner")
        .groupBy("genre_group")
        .agg(
            F.count("*").alias("movie_count"),
            F.round(F.avg("rating"), 2).alias("avg_rating"),
            F.sum("vote_count").alias("rating_votes"),
        )
        .orderBy(F.desc("movie_count"))
        .show(truncate=False)
    )


def read_movies(spark, input_path):
    return (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .option("multiLine", True)
        .option("quote", '"')
        .option("escape", '"')
        .csv(input_path)
    )


def run_timed_query(spark, input_path) -> None:
    print("===== PERFORMANCE QUERY: END-TO-END LOAD, CLEAN AND GENRE AGGREGATION TIMINGS =====")
    for run in range(1, 4):
        start = time.perf_counter()
        performance_df = clean_movies(read_movies(spark, input_path))
        rows = genre_aggregate(performance_df).collect()
        elapsed = time.perf_counter() - start
        print(f"PERF_RUN run={run} seconds={elapsed:.6f} result_rows={len(rows)}")


if __name__ == "__main__":
    main()
