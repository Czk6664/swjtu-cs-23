from __future__ import annotations

import numpy as np


LAPLACIAN_KERNEL = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], dtype=np.float64)
SOBEL_X_KERNEL = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
SOBEL_Y_KERNEL = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)


def _convolve(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    kernel_size = kernel.shape[0]
    pad = kernel_size // 2
    padded = np.pad(image, pad_width=pad, mode='edge').astype(np.float64)
    result = np.zeros_like(image, dtype=np.float64)

    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            patch = padded[row : row + kernel_size, col : col + kernel_size]
            result[row, col] = np.sum(patch * kernel)

    return result


def laplacian_sharpen(image: np.ndarray, alpha: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    laplacian_response = _convolve(image, LAPLACIAN_KERNEL)
    sharpened = image.astype(np.float64) + alpha * laplacian_response
    clipped = np.clip(np.round(sharpened), 0, 255).astype(np.uint8)
    response = np.clip(np.abs(np.round(laplacian_response)), 0, 255).astype(np.uint8)
    return response, clipped


def sobel_sharpen(image: np.ndarray, alpha: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    gradient_x = _convolve(image, SOBEL_X_KERNEL)
    gradient_y = _convolve(image, SOBEL_Y_KERNEL)
    gradient = np.hypot(gradient_x, gradient_y)
    sharpened = image.astype(np.float64) + alpha * gradient
    clipped = np.clip(np.round(sharpened), 0, 255).astype(np.uint8)
    response = np.clip(np.round(gradient), 0, 255).astype(np.uint8)
    return response, clipped
