from pathlib import Path
from statistics import mean, stdev
import json
import re

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).parent
LOG = BASE / "data" / "douban-analysis-v4-2exec.log"
LOG_ONE = BASE / "data" / "douban-analysis-v4-1exec.log"
PODS = BASE / "data" / "douban-v4-running-pods.txt"
PANDAS = BASE / "data" / "pandas_douban_timings.json"
FIGURES = BASE.parent.parent / "cloud-report-tex" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def lines_between(lines, start_text, end_text=None):
    start = next(i for i, line in enumerate(lines) if start_text in line)
    if end_text is None:
        return lines[start:]
    end = next((i for i in range(start + 1, len(lines)) if end_text in lines[i]), len(lines))
    return lines[start:end]


def terminal_image(name, title, body_lines):
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 25)
        bold = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 27)
    except OSError:
        font = ImageFont.load_default()
        bold = font
    width = 2460
    line_height = 39
    height = 74 + line_height * len(body_lines) + 36
    image = Image.new("RGB", (width, height), "#0f1319")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 57), fill="#262c35")
    draw.text((28, 13), title, font=bold, fill="#f5f7fb")
    y = 76
    for line in body_lines:
        color = "#d9e0ea"
        if line.startswith("====="):
            color = "#7cc4ff"
        if "PERF_RUN" in line or "COMPLETED" in line or "Running" in line:
            color = "#6ee7b7"
        draw.text((30, y), line.rstrip(), font=font, fill=color)
        y += line_height
    image.save(FIGURES / name)


def timing_values(path):
    text = path.read_text(encoding="utf-8-sig")
    return [float(value) for value in re.findall(r"PERF_RUN run=\d+ seconds=([0-9.]+)", text)]


def performance_chart():
    pandas = [float(row["seconds"]) for row in json.loads(PANDAS.read_text(encoding="utf-8"))]
    spark_one = timing_values(LOG_ONE)
    spark_two = timing_values(LOG)
    datasets = [pandas, spark_one, spark_two]
    labels = ["Pandas\n(single node)", "PySpark\n(1 executor)", "PySpark\n(2 executors)"]
    means = [mean(values) for values in datasets]
    errors = [stdev(values) for values in datasets]
    colors = ["#697386", "#2f6fdb", "#16a085"]
    baseline = means[0]

    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=220)
    bars = ax.bar(labels, means, yerr=errors, capsize=6, width=0.58, color=colors,
                  edgecolor="#172033", linewidth=1.0)
    ax.set_ylabel("End-to-end execution time (s)", fontsize=12)
    ax.set_xlabel("Execution mode", fontsize=12)
    ax.set_title("Official Douban Dataset: Genre Aggregation Performance", fontsize=17, weight="bold", pad=15)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, max(means) + max(errors) + 0.34)
    for bar, value in zip(bars, means):
        speedup = baseline / value
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.12,
                f"{value:.3f}s\n{speedup:.2f}x", ha="center", va="bottom", fontsize=11)
    fig.text(0.5, 0.01, "Bars show the mean of three end-to-end runs; error bars indicate one standard deviation.",
             ha="center", fontsize=10, color="#4b5563")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIGURES / "a3-performance-comparison.png", bbox_inches="tight")
    fig.savefig(FIGURES / "a3-performance-comparison.pdf", bbox_inches="tight")


def main():
    lines = LOG.read_text(encoding="utf-8-sig").splitlines()
    pods = PODS.read_text(encoding="utf-8-sig").splitlines()
    terminal_image("a1-douban-pods.png", "kubectl get pods -o wide  |  official Douban Spark job", pods)
    terminal_image(
        "a1-schema-firstrows-official.png",
        "kubectl logs pyspark-douban-analysis-driver  |  schema and first five rows",
        lines_between(lines, "===== OFFICIAL DATASET SCHEMA =====", "===== RAW ROW COUNT"),
    )
    terminal_image(
        "a1-cleaning-official.png",
        "kubectl logs pyspark-douban-analysis-driver  |  missing values and row cleaning",
        lines_between(lines, "===== RAW ROW COUNT", "===== QUERY 1"),
    )
    terminal_image(
        "a2-groupby-genre-official.png",
        "Spark SQL / DataFrame output  |  GROUP BY exploded genre",
        lines_between(lines, "===== QUERY 1", "===== QUERY 2"),
    )
    terminal_image(
        "a2-topn-rating-official.png",
        "Spark SQL / DataFrame output  |  ORDER BY Top-N",
        lines_between(lines, "===== QUERY 2", "===== QUERY 3"),
    )
    terminal_image(
        "a2-year-trend-official.png",
        "Spark SQL / DataFrame output  |  time trend",
        lines_between(lines, "===== QUERY 3", "===== QUERY 4"),
    )
    terminal_image(
        "a2-window-ranking-official.png",
        "Spark SQL / DataFrame output  |  window function",
        lines_between(lines, "===== QUERY 4", "===== QUERY 5"),
    )
    terminal_image(
        "a2-join-genre-group-official.png",
        "Spark SQL / DataFrame output  |  dimension JOIN",
        lines_between(lines, "===== QUERY 5", "===== PERFORMANCE QUERY"),
    )
    performance_chart()


if __name__ == "__main__":
    main()
