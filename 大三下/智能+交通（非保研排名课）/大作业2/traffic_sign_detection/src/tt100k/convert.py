from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from PIL import Image

from .classes import get_source_to_index


@dataclass(frozen=True)
class ConvertedSample:
    image_id: str
    image_path: Path
    label_lines: List[str]


class TT100KFormatError(ValueError):
    pass



def load_annotations(annotation_path: Path) -> Dict:
    with annotation_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TT100KFormatError("annotation file must contain a JSON object")
    return payload



def iter_objects(image_record: Dict) -> Iterable[Dict]:
    objects = image_record.get("objects", [])
    if not isinstance(objects, list):
        raise TT100KFormatError("image record field 'objects' must be a list")
    return objects



def bbox_to_yolo(size: tuple[int, int], bbox: Dict[str, float]) -> tuple[float, float, float, float]:
    width, height = size
    xmin = float(bbox["xmin"])
    ymin = float(bbox["ymin"])
    xmax = float(bbox["xmax"])
    ymax = float(bbox["ymax"])

    x_center = ((xmin + xmax) / 2.0) / width
    y_center = ((ymin + ymax) / 2.0) / height
    box_width = (xmax - xmin) / width
    box_height = (ymax - ymin) / height
    return x_center, y_center, box_width, box_height



def convert_image_record(image_id: str, image_record: Dict, image_path: Path) -> ConvertedSample:
    width = image_record.get("width")
    height = image_record.get("height")
    if width is None or height is None:
        with Image.open(image_path) as image:
            width, height = image.size
    width = int(width)
    height = int(height)
    class_map = get_source_to_index()
    label_lines: List[str] = []

    for obj in iter_objects(image_record):
        category = obj.get("category")
        if category not in class_map:
            continue
        bbox = obj.get("bbox")
        if not isinstance(bbox, dict):
            raise TT100KFormatError(f"image {image_id} has invalid bbox")
        x_center, y_center, box_width, box_height = bbox_to_yolo((width, height), bbox)
        label_lines.append(
            f"{class_map[category]} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"
        )

    return ConvertedSample(image_id=image_id, image_path=image_path, label_lines=label_lines)
