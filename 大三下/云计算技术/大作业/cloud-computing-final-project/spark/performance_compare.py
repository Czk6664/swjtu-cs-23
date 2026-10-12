import argparse
import csv
import json
from pathlib import Path
from statistics import mean


def load_timings(path: Path) -> list[dict[str, float | str]]:
    with path.open("r", encoding="utf-8") as f:
        rows = json.load(f)
    return rows


def summarize(rows: list[dict[str, float | str]]) -> list[dict[str, float | str]]:
    grouped: dict[str, list[float]] = {}
    for row in rows:
        grouped.setdefault(str(row["mode"]), []).append(float(row["seconds"]))

    baseline = mean(grouped["pandas"])
    summary = []
    for mode, values in grouped.items():
        avg = mean(values)
        summary.append(
            {
                "mode": mode,
                "avg_seconds": round(avg, 4),
                "speedup_vs_pandas": round(baseline / avg, 4) if avg else 0,
                "runs": len(values),
            }
        )
    return summary


def write_csv(summary: list[dict[str, float | str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["mode", "avg_seconds", "speedup_vs_pandas", "runs"])
        writer.writeheader()
        writer.writerows(summary)


def maybe_write_chart(summary: list[dict[str, float | str]], output: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; CSV summary was still generated.")
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    modes = [str(row["mode"]) for row in summary]
    seconds = [float(row["avg_seconds"]) for row in summary]
    speedups = [float(row["speedup_vs_pandas"]) for row in summary]

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.bar(modes, seconds, color="#4c78a8", label="Average seconds")
    ax1.set_ylabel("Average execution time / s")
    ax1.set_xlabel("Execution mode")

    ax2 = ax1.twinx()
    ax2.plot(modes, speedups, color="#f58518", marker="o", label="Speedup")
    ax2.set_ylabel("Speedup vs Pandas")

    fig.suptitle("Pandas vs PySpark Performance Comparison")
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    print(f"Chart written to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Pandas/PySpark timing records.")
    parser.add_argument("--input", default="data/performance_timings.json")
    parser.add_argument("--csv", default="../report/charts/performance-summary.csv")
    parser.add_argument("--chart", default="../report/charts/performance-comparison.png")
    args = parser.parse_args()

    rows = load_timings(Path(args.input))
    summary = summarize(rows)
    write_csv(summary, Path(args.csv))
    maybe_write_chart(summary, Path(args.chart))

    print("===== PERFORMANCE SUMMARY =====")
    for row in summary:
        print(row)


if __name__ == "__main__":
    main()
