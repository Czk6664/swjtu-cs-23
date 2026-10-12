from __future__ import annotations

import numpy as np


def _validate_kernel_size(kernel_size: int) -> None:
    if kernel_size <= 0 or kernel_size % 2 == 0:
        raise ValueError("kernel_size must be a positive odd integer")


def _pad_image(image: np.ndarray, kernel_size: int) -> np.ndarray:
    pad = kernel_size // 2
    return np.pad(image, pad_width=pad, mode="edge")


def linear_smoothing_filter(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Smooth an image with a mean kernel."""
    _validate_kernel_size(kernel_size)
    padded = _pad_image(image, kernel_size).astype(np.float64)
    result = np.zeros_like(image, dtype=np.float64)

    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            patch = padded[row : row + kernel_size, col : col + kernel_size]
            result[row, col] = patch.mean()

    return np.clip(np.round(result), 0, 255).astype(np.uint8)


def order_statistic_filter(image: np.ndarray, kernel_size: int = 3, mode: str = "median") -> np.ndarray:
    """Apply a median, min, or max order-statistic filter."""
    _validate_kernel_size(kernel_size)
    padded = _pad_image(image, kernel_size)
    result = np.zeros_like(image, dtype=np.float64)

    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            values = padded[row : row + kernel_size, col : col + kernel_size].reshape(-1)
            if mode == "median":
                result[row, col] = np.median(values)
            elif mode == "min":
                result[row, col] = values.min()
            elif mode == "max":
                result[row, col] = values.max()
            else:
                raise ValueError("mode must be 'median', 'min', or 'max'")

    return np.clip(np.round(result), 0, 255).astype(np.uint8)


mean_filter = linear_smoothing_filter
