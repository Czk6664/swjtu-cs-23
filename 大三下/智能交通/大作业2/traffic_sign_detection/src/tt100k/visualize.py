from __future__ import annotations

from pathlib import Path
from typing import Iterable

import cv2



def draw_boxes(image_path: Path, boxes: Iterable[tuple[int, int, int, int, str]], output_path: Path) -> None:
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"unable to read image: {image_path}")

    for xmin, ymin, xmax, ymax, label in boxes:
        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        cv2.putText(image, label, (xmin, max(ymin - 4, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image)
