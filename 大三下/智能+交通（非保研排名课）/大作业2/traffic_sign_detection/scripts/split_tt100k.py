from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from prepare_tt100k import convert_dataset, resolve_annotation_path, resolve_image_roots


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recreate TT100K train/val/test split in YOLO layout.")
    parser.add_argument("--src", required=True, help="Path to raw TT100K dataset root")
    parser.add_argument("--dest", required=True, help="Path to YOLO-format output dataset root")
    parser.add_argument("--annotations", default="annotations_all.json")
    parser.add_argument("--images-dir", default="train,test,other")
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    src_root = Path(args.src).resolve()
    dest_root = Path(args.dest).resolve()
    summary = convert_dataset(
        src_root=src_root,
        dest_root=dest_root,
        annotations_path=resolve_annotation_path(src_root, args.annotations),
        image_roots=resolve_image_roots(src_root, args.images_dir),
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )
    print(summary)


if __name__ == "__main__":
    main()
