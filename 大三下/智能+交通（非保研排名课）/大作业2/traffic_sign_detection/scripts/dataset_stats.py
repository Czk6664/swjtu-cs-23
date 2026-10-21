from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List

import yaml


SPLITS = ("train", "val", "test")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize a YOLO-format TT100K dataset.")
    parser.add_argument("--data", default="configs/dataset/tt100k.yaml", help="Path to YOLO dataset yaml")
    parser.add_argument("--output-dir", default="outputs/report_assets/dataset", help="Directory for statistics")
    return parser.parse_args()


def load_dataset_config(path: Path) -> Dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def resolve_dataset_root(config_path: Path, config: Dict) -> Path:
    dataset_root = Path(config["path"])
    if not dataset_root.is_absolute():
        dataset_root = config_path.parent / dataset_root
    return dataset_root.resolve()


def count_images(path: Path) -> int:
    suffixes = {".jpg", ".jpeg", ".png", ".bmp"}
    if not path.exists():
        return 0
    return sum(1 for item in path.iterdir() if item.is_file() and item.suffix.lower() in suffixes)


def count_split(labels_dir: Path, class_count: int) -> Counter:
    counts: Counter = Counter()
    if not labels_dir.exists():
        return counts

    for label_file in labels_dir.glob("*.txt"):
        for line in label_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            class_id = int(line.split()[0])
            if 0 <= class_id < class_count:
                counts[class_id] += 1
    return counts


def build_summary(config_path: Path) -> Dict:
    config = load_dataset_config(config_path)
    names: List[str] = list(config["names"])
    root = resolve_dataset_root(config_path, config)
    source_to_target = config.get("source_to_target", {})

    split_rows = []
    per_class_rows = []
    total_counts: Counter = Counter()

    for split in SPLITS:
        images_dir = root / "images" / split
        labels_dir = root / "labels" / split
        split_counts = count_split(labels_dir, len(names))
        total_counts.update(split_counts)
        split_rows.append(
            {
                "split": split,
                "images": count_images(images_dir),
                "label_files": len(list(labels_dir.glob("*.txt"))) if labels_dir.exists() else 0,
                "objects": sum(split_counts.values()),
            }
        )
        for class_id, class_name in enumerate(names):
            per_class_rows.append(
                {
                    "split": split,
                    "class_id": class_id,
                    "class_name": class_name,
                    "source_name": next((src for src, target in source_to_target.items() if target == class_name), ""),
                    "objects": split_counts[class_id],
                }
            )

    total_rows = [
        {
            "class_id": class_id,
            "class_name": class_name,
            "source_name": next((src for src, target in source_to_target.items() if target == class_name), ""),
            "objects": total_counts[class_id],
        }
        for class_id, class_name in enumerate(names)
    ]
    return {
        "dataset_root": str(root),
        "class_count": len(names),
        "nonempty_class_count": sum(1 for row in total_rows if row["objects"] > 0),
        "split_rows": split_rows,
        "per_class_rows": per_class_rows,
        "total_rows": total_rows,
    }


def write_csv(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_latex_table(path: Path, summary: Dict) -> None:
    lines = [
        r"\begin{tabular}{llr}",
        r"\toprule",
        r"TT100K原始类别 & 训练类别名 & 目标框数量 \\",
        r"\midrule",
    ]
    for row in summary["total_rows"]:
        escaped_name = row["class_name"].replace("_", r"\_")
        lines.append(f"{row['source_name']} & {escaped_name} & {row['objects']} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    config_path = Path(args.data).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = build_summary(config_path)
    (output_dir / "dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(output_dir / "split_counts.csv", summary["split_rows"])
    write_csv(output_dir / "per_class_counts.csv", summary["per_class_rows"])
    write_csv(output_dir / "class_totals.csv", summary["total_rows"])
    write_latex_table(output_dir / "class_totals_table.tex", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
