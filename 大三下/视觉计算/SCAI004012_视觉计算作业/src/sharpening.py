from __future__ import annotations

import numpy as np


LAPLACIAN_KERNEL = np.array(
    [[0, -1, 0], [-1, 4, -1], [0, -1, 0]],
    dtype=np.float64,
)
SOBEL_X_KERNEL = np.array(
    [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
    dtype=np.float64,
)
SOBEL_Y_KERNEL = np.array(
    [[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
    dtype=np.float64,
)


def convolve2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Convolve a grayscale image with a square kernel using edge padding."""
    if image.ndim != 2:
        raise ValueError("convolve2d expects a grayscale image")
    if kernel.ndim != 2 or kernel.shape[0] != kernel.shape[1] or kernel.shape[0] % 2 == 0:
        raise ValueError("kernel must be square with odd side length")

    kernel_size = kernel.shape[0]
    pad = kernel_size // 2
    padded = np.pad(image, pad_width=pad, mode="edge").astype(np.float64)
    result = np.zeros_like(image, dtype=np.float64)

    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            patch = padded[row : row + kernel_size, col : col + kernel_size]
            result[row, col] = np.sum(patch * kernel)

    return result


def laplacian_sharpen(image: np.ndarray, alpha: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Sharpen by adding the Laplacian response to the original image."""
    response = convolve2d(image, LAPLACIAN_KERNEL)
    sharpened = image.astype(np.float64) + alpha * response
    response_view = np.clip(np.abs(np.round(response)), 0, 255).astype(np.uint8)
    result = np.clip(np.round(sharpened), 0, 255).astype(np.uint8)
    return response_view, result


def sobel_gradient(image: np.ndarray) -> np.ndarray:
    """Return first-order Sobel gradient magnitude."""
    gradient_x = convolve2d(image, SOBEL_X_KERNEL)
    gradient_y = convolve2d(image, SOBEL_Y_KERNEL)
    return np.hypot(gradient_x, gradient_y)


def sobel_sharpen(image: np.ndarray, alpha: float = 0.6) -> tuple[np.ndarray, np.ndarray]:
    """Sharpen by adding first-order Sobel gradient magnitude."""
    gradient = sobel_gradient(image)
    sharpened = image.astype(np.float64) + alpha * gradient
    response_view = np.clip(np.round(gradient), 0, 255).astype(np.uint8)
    result = np.clip(np.round(sharpened), 0, 255).astype(np.uint8)
    return response_view, result
