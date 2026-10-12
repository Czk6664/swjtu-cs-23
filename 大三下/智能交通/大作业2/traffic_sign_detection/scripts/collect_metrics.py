from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect validation metrics into CSV and JSON.")
    parser.add_argument("--results-dir", required=True, help="Directory containing val outputs")
    parser.add_argument("--output-dir", default="outputs/report_assets/metrics")
    return parser.parse_args()


def load_metrics(results_dir: Path) -> Dict[str, float]:
    results_json = results_dir / "metrics.json"
    if results_json.exists():
        return json.loads(results_json.read_text(encoding="utf-8"))

    fallback_csv = results_dir / "results.csv"
    if fallback_csv.exists():
        with fallback_csv.open("r", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            return {}
        latest = rows[-1]
        return {key: float(value) for key, value in latest.items() if value not in ("", None)}

    raise FileNotFoundError("No metrics.json or results.csv found in results directory")


def save_csv(metrics: Dict[str, float], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        for key, value in metrics.items():
            writer.writerow([key, value])


def main() -> None:
    args = parse_args()
    results_dir = Path(args.results_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    metrics = load_metrics(results_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    save_csv(metrics, output_dir / "metrics.csv")
    print(output_dir)


if __name__ == "__main__":
    main()
