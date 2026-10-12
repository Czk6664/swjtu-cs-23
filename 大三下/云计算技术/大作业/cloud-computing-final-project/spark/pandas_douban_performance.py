import json
import time
from pathlib import Path

import pandas as pd


INPUT_PATH = Path(__file__).parent / "data" / "douban_movies.csv"
OUTPUT_PATH = Path(__file__).parent / "data" / "pandas_douban_timings.json"


def genre_aggregation() -> pd.DataFrame:
    raw = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
    cleaned = raw.dropna(subset=["rating_score"]).loc[lambda data: data["rating_score"] > 0].copy()
    cleaned["genres"] = cleaned["genres"].fillna("未知类型")
    exploded = cleaned.assign(single_genre=cleaned["genres"].str.split("/")).explode("single_genre")
    exploded["single_genre"] = exploded["single_genre"].str.strip()
    return (
        exploded.groupby("single_genre", as_index=False)
        .agg(
            movie_count=("movie_id", "count"),
            avg_rating=("rating_score", "mean"),
            rating_votes=("rating_count", "sum"),
        )
        .sort_values(["movie_count", "avg_rating"], ascending=[False, False])
    )


def main() -> None:
    genre_aggregation()
    timings = []
    for run in range(1, 4):
        start = time.perf_counter()
        result = genre_aggregation()
        elapsed = time.perf_counter() - start
        timings.append({"mode": "pandas", "run": run, "seconds": round(elapsed, 6)})
        print(f"PERF_RUN mode=pandas run={run} seconds={elapsed:.6f} result_rows={len(result)}")

    OUTPUT_PATH.write_text(json.dumps(timings, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
