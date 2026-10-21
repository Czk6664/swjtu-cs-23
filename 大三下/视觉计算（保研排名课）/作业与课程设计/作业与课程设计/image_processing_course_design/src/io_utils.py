from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def ensure_dir(path: str | Path) -> Path:
    output_path = Path(path)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def load_image(path: str | Path, grayscale: bool = False) -> np.ndarray:
    image = Image.open(path)
    if grayscale:
        image = image.convert('L')
    return np.array(image)


def save_image(path: str | Path, image: np.ndarray) -> None:
    output = np.clip(image, 0, 255).astype(np.uint8)
    Image.fromarray(output).save(path)


def normalize_to_uint8(image: np.ndarray) -> np.ndarray:
    image = image.astype(np.float64)
    min_value = float(image.min())
    max_value = float(image.max())
    if max_value == min_value:
        return np.zeros_like(image, dtype=np.uint8)
    normalized = (image - min_value) / (max_value - min_value)
    return np.round(normalized * 255.0).astype(np.uint8)


def save_histogram_plot(path: str | Path, image: np.ndarray, title: str) -> None:
    plt.figure(figsize=(6, 4))
    plt.hist(image.ravel(), bins=256, range=(0, 255), color='steelblue')
    plt.title(title)
    plt.xlabel('Pixel value')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def save_comparison_grid(path: str | Path, images: Iterable[np.ndarray], titles: Iterable[str], cmap: str | None = None) -> None:
    image_list = list(images)
    title_list = list(titles)
    columns = len(image_list)
    plt.figure(figsize=(4 * columns, 4))
    for index, (image, title) in enumerate(zip(image_list, title_list), start=1):
        plt.subplot(1, columns, index)
        if image.ndim == 2:
            plt.imshow(image, cmap=cmap or 'gray')
        else:
            plt.imshow(image)
        plt.title(title)
        plt.axis('off')
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
