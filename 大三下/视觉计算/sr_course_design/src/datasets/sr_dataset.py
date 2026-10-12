"""Minimal dataset and image utilities for super-resolution course project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image


VALID_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}


@dataclass(frozen=True)
class ImagePair:
    """Store low-resolution and high-resolution image paths."""

    lr_path: Path
    hr_path: Path


@dataclass(frozen=True)
class DatasetConfig:
    """Dataset configuration for training or evaluation."""

    root_dir: Path
    lr_dirname: str = "LR"
    hr_dirname: str = "HR"
    scale: int = 2


@dataclass(frozen=True)
class LoadedImagePair:
    """Store loaded low-resolution and high-resolution image arrays."""

    filename: str
    lr_image: np.ndarray
    hr_image: np.ndarray


def list_image_pairs(config: DatasetConfig) -> list[ImagePair]:
    """Collect LR/HR image pairs by matching filenames."""

    lr_dir = config.root_dir / config.lr_dirname
    hr_dir = config.root_dir / config.hr_dirname

    if not lr_dir.exists() or not hr_dir.exists():
        return []

    hr_map = {
        path.name: path
        for path in hr_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VALID_IMAGE_EXTENSIONS
    }
    pairs = [
        ImagePair(lr_path=lr_path, hr_path=hr_map[lr_path.name])
        for lr_path in lr_dir.iterdir()
        if lr_path.is_file()
        and lr_path.suffix.lower() in VALID_IMAGE_EXTENSIONS
        and lr_path.name in hr_map
    ]
    return sorted(pairs, key=lambda pair: pair.lr_path.name)


def load_image(image_path: str | Path) -> np.ndarray:
    """Load an RGB image as an HWC uint8 array."""

    with Image.open(image_path) as image:
        return np.array(image.convert("RGB"), dtype=np.uint8)


def save_image(image: np.ndarray, image_path: str | Path) -> None:
    """Save an image array to disk."""

    output_path = Path(image_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image).save(output_path)


def load_image_pair(pair: ImagePair) -> LoadedImagePair:
    """Load one LR/HR pair from disk."""

    return LoadedImagePair(
        filename=pair.lr_path.name,
        lr_image=load_image(pair.lr_path),
        hr_image=load_image(pair.hr_path),
    )


def load_image_pairs(config: DatasetConfig) -> list[LoadedImagePair]:
    """Load all LR/HR pairs into memory."""

    return [load_image_pair(pair) for pair in list_image_pairs(config)]


def random_patch(lr_image: np.ndarray, hr_image: np.ndarray, patch_size: int, scale: int) -> tuple[np.ndarray, np.ndarray]:
    """Crop aligned LR/HR patches for training."""

    lr_height, lr_width = lr_image.shape[:2]
    hr_height, hr_width = hr_image.shape[:2]
    if hr_height != lr_height * scale or hr_width != lr_width * scale:
        raise ValueError(
            "LR/HR image shapes are not aligned with the configured scale: "
            f"LR={lr_image.shape}, HR={hr_image.shape}, scale={scale}"
        )

    if lr_height < patch_size or lr_width < patch_size:
        return lr_image, hr_image

    top = np.random.randint(0, lr_height - patch_size + 1)
    left = np.random.randint(0, lr_width - patch_size + 1)
    hr_top = top * scale
    hr_left = left * scale

    lr_patch = lr_image[top : top + patch_size, left : left + patch_size]
    hr_patch = hr_image[
        hr_top : hr_top + patch_size * scale,
        hr_left : hr_left + patch_size * scale,
    ]
    return lr_patch, hr_patch


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalize image array into [0, 1]."""

    return image.astype(np.float32) / 255.0


def denormalize_image(image: np.ndarray) -> np.ndarray:
    """Convert normalized image array back to uint8."""

    clipped = np.clip(image * 255.0, 0.0, 255.0)
    return clipped.astype(np.uint8)


def hwc_to_chw(image: np.ndarray) -> np.ndarray:
    """Convert an HWC image into CHW layout."""

    return np.transpose(image, (2, 0, 1))


def chw_to_hwc(image: np.ndarray) -> np.ndarray:
    """Convert a CHW image into HWC layout."""

    return np.transpose(image, (1, 2, 0))


def image_to_tensor(image: np.ndarray) -> np.ndarray:
    """Convert uint8 HWC image into float32 CHW tensor data."""

    return hwc_to_chw(normalize_image(image)).astype(np.float32)


def tensor_to_image(tensor: np.ndarray) -> np.ndarray:
    """Convert CHW or NCHW tensor data into uint8 HWC image."""

    if tensor.ndim == 4:
        tensor = tensor[0]
    return denormalize_image(chw_to_hwc(np.clip(tensor, 0.0, 1.0)))


def iter_filenames(paths: Iterable[ImagePair]) -> list[str]:
    """Return ordered filenames for logging or result export."""

    return [pair.lr_path.name for pair in paths]
