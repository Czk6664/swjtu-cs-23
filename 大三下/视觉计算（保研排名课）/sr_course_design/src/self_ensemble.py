"""Deterministic self-ensemble utilities for super-resolution inference."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class EnsembleTransform:
    """A reversible HWC image transform."""

    name: str
    rotation: int = 0
    flip_horizontal: bool = False
    flip_vertical: bool = False


ENSEMBLE_TRANSFORMS: tuple[EnsembleTransform, ...] = (
    EnsembleTransform("identity"),
    EnsembleTransform("rot90", rotation=1),
    EnsembleTransform("rot180", rotation=2),
    EnsembleTransform("rot270", rotation=3),
    EnsembleTransform("hflip", flip_horizontal=True),
    EnsembleTransform("hflip_rot90", rotation=1, flip_horizontal=True),
    EnsembleTransform("vflip", flip_vertical=True),
    EnsembleTransform("vflip_rot90", rotation=1, flip_vertical=True),
)


def apply_transform(image: np.ndarray, transform: EnsembleTransform) -> np.ndarray:
    """Apply a deterministic transform to an HWC image or feature map."""

    transformed = np.rot90(image, k=transform.rotation, axes=(0, 1))
    if transform.flip_horizontal:
        transformed = np.flip(transformed, axis=1)
    if transform.flip_vertical:
        transformed = np.flip(transformed, axis=0)
    return np.ascontiguousarray(transformed)


def invert_transform(image: np.ndarray, transform: EnsembleTransform) -> np.ndarray:
    """Invert a transform created by apply_transform."""

    restored = image
    if transform.flip_vertical:
        restored = np.flip(restored, axis=0)
    if transform.flip_horizontal:
        restored = np.flip(restored, axis=1)
    restored = np.rot90(restored, k=-transform.rotation, axes=(0, 1))
    return np.ascontiguousarray(restored)


def average_predictions(predictions: list[np.ndarray]) -> np.ndarray:
    """Average HWC float predictions and clip to [0, 1]."""

    if not predictions:
        raise ValueError("No predictions were provided for self-ensemble averaging.")
    reference_shape = predictions[0].shape
    for prediction in predictions:
        if prediction.shape != reference_shape:
            raise ValueError(f"Prediction shape mismatch: {prediction.shape} vs {reference_shape}")
    return np.clip(np.mean(np.stack(predictions, axis=0), axis=0), 0.0, 1.0)
