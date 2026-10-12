from __future__ import annotations

import numpy as np


def _pad_image(image: np.ndarray, kernel_size: int) -> np.ndarray:
    pad = kernel_size // 2
    return np.pad(image, pad_width=pad, mode='edge')


def mean_filter(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    if kernel_size % 2 == 0:
        raise ValueError('kernel_size must be odd')
    padded = _pad_image(image, kernel_size)
    result = np.zeros_like(image, dtype=np.float64)

    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            patch = padded[row : row + kernel_size, col : col + kernel_size]
            result[row, col] = patch.mean()

    return np.clip(np.round(result), 0, 255).astype(np.uint8)


def order_statistic_filter(image: np.ndarray, kernel_size: int = 3, mode: str = 'median') -> np.ndarray:
    if kernel_size % 2 == 0:
        raise ValueError('kernel_size must be odd')
    padded = _pad_image(image, kernel_size)
    result = np.zeros_like(image, dtype=np.float64)

    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            patch = padded[row : row + kernel_size, col : col + kernel_size].reshape(-1)
            if mode == 'median':
                result[row, col] = np.median(patch)
            elif mode == 'max':
                result[row, col] = patch.max()
            elif mode == 'min':
                result[row, col] = patch.min()
            else:
                raise ValueError('mode must be median, max, or min')

    return np.clip(np.round(result), 0, 255).astype(np.uint8)
