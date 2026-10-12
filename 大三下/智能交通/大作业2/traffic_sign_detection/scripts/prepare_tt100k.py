from __future__ import annotations

import argparse
import random
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml

from src.tt100k.classes import get_class_names, get_source_to_target
from src.tt100k.convert import ConvertedSample, convert_image_record, load_annotations

VALID_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".bmp")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert TT100K annotations into YOLO format.")
    parser.add_argument("--src", required=True, help="Path to raw TT100K dataset root")
    parser.add_argument("--dest", required=True, help="Path to YOLO-format output dataset root")
    parser.add_argument("--annotations", default="annotations_all.json", help="Annotation JSON path relative to --src if not absolute")
    parser.add_argument(
        "--images-dir",
        default="train,test,other",
        help="Comma-separated image directories relative to --src if not absolute",
    )
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def resolve_input_path(root: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def resolve_annotation_path(root: Path, value: str) -> Path:
    candidate = resolve_input_path(root, value)
    if candidate.exists():
        return candidate

    fallback = root / "annotations_all.json"
    if fallback.exists():
        return fallback

    raise FileNotFoundError(f"annotation file not found: {candidate}")


def resolve_image_roots(root: Path, value: str) -> List[Path]:
    image_roots: List[Path] = []
    for part in (item.strip() for item in value.split(",")):
        if not part:
            continue
        candidate = resolve_input_path(root, part)
        if candidate.exists():
            image_roots.append(candidate)
    if image_roots:
        return image_roots

    fallback = [root / name for name in ("train", "test", "other") if (root / name).exists()]
    if fallback:
        return fallback

    raise FileNotFoundError(f"image directories not found from input: {value}")


def ensure_output_layout(dest_root: Path) -> None:
    for split in ("train", "val", "test"):
        (dest_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (dest_root / "labels" / split).mkdir(parents=True, exist_ok=True)


def build_image_index(image_roots: List[Path]) -> Dict[str, Path]:
    image_index: Dict[str, Path] = {}
    for image_root in image_roots:
        for path in image_root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in VALID_IMAGE_SUFFIXES:
                continue
            image_index.setdefault(path.stem, path)
    return image_index


def find_image_path(image_index: Dict[str, Path], image_id: str) -> Path:
    candidate = image_index.get(image_id)
    if candidate is not None:
        return candidate
    for suffix in VALID_IMAGE_SUFFIXES:
        candidate = image_index.get(f"{image_id}{suffix}")
        if candidate is not None:
            return candidate
    raise FileNotFoundError(f"image file not found for image id: {image_id}")


def split_ids(image_ids: List[str], val_ratio: float, test_ratio: float, seed: int) -> Dict[str, List[str]]:
    shuffled = list(image_ids)
    random.Random(seed).shuffle(shuffled)
    total = len(shuffled)
    test_count = int(total * test_ratio)
    val_count = int(total * val_ratio)
    test_ids = shuffled[:test_count]
    val_ids = shuffled[test_count:test_count + val_count]
    train_ids = shuffled[test_count + val_count:]
    return {"train": train_ids, "val": val_ids, "test": test_ids}


def write_label_file(label_path: Path, sample: ConvertedSample) -> None:
    label_path.parent.mkdir(parents=True, exist_ok=True)
    label_path.write_text("\n".join(sample.label_lines), encoding="utf-8")


def copy_image(sample: ConvertedSample, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample.image_path, target_path)


def create_dataset_yaml(dest_root: Path) -> Dict:
    return {
        "path": str(dest_root.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": get_class_names(),
        "source_to_target": get_source_to_target(),
    }


def save_dataset_yaml(dataset_yaml: Dict) -> None:
    config_dir = Path(__file__).resolve().parents[1] / "configs" / "dataset"
    config_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = config_dir / "tt100k.yaml"
    yaml_path.write_text(yaml.safe_dump(dataset_yaml, allow_unicode=True, sort_keys=False), encoding="utf-8")


def convert_dataset(src_root: Path, dest_root: Path, annotations_path: Path, image_roots: List[Path], val_ratio: float, test_ratio: float, seed: int) -> Dict[str, int]:
    annotations = load_annotations(annotations_path)
    image_records = annotations.get("imgs", annotations)
    if not isinstance(image_records, dict):
        raise ValueError("TT100K annotations must expose an image record dictionary")
    image_index = build_image_index(image_roots)

    filtered_samples: List[Tuple[str, ConvertedSample]] = []
    skipped_empty = 0
    missing_images = 0

    for image_id, image_record in image_records.items():
        try:
            image_path = find_image_path(image_index, image_id)
        except FileNotFoundError:
            missing_images += 1
            continue
        sample = convert_image_record(image_id=image_id, image_record=image_record, image_path=image_path)
        if not sample.label_lines:
            skipped_empty += 1
            continue
        filtered_samples.append((image_id, sample))

    split_mapping = split_ids([image_id for image_id, _ in filtered_samples], val_ratio, test_ratio, seed)
    sample_map = {image_id: sample for image_id, sample in filtered_samples}
    ensure_output_layout(dest_root)

    for split, image_ids in split_mapping.items():
        for image_id in image_ids:
            sample = sample_map[image_id]
            target_image = dest_root / "images" / split / f"{image_id}{sample.image_path.suffix}"
            target_label = dest_root / "labels" / split / f"{image_id}.txt"
            copy_image(sample, target_image)
            write_label_file(target_label, sample)

    save_dataset_yaml(create_dataset_yaml(dest_root))
    return {
        "train": len(split_mapping["train"]),
        "val": len(split_mapping["val"]),
        "test": len(split_mapping["test"]),
        "skipped_empty": skipped_empty,
        "missing_images": missing_images,
        "indexed_images": len(image_index),
    }


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
