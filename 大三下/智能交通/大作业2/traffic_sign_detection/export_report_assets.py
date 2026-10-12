from __future__ import annotations

import argparse
import shutil
from pathlib import Path



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export figures and metrics for the LaTeX report.")
    parser.add_argument("--from-dir", required=True, help="Directory containing generated figures and metrics")
    parser.add_argument("--to-dir", default="outputs/report_assets/final")
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    source_dir = Path(args.from_dir).resolve()
    target_dir = Path(args.to_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(source_dir)
        destination = target_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

    print(target_dir)


if __name__ == "__main__":
    main()
