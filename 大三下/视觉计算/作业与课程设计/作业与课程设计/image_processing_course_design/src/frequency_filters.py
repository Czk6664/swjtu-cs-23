from __future__ import annotations

import numpy as np


def compute_frequency_spectrum(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    frequency = np.fft.fftshift(np.fft.fft2(image))
    magnitude = np.log1p(np.abs(frequency))
    return frequency, magnitude


def _distance_mask(shape: tuple[int, int], cutoff: float, high_pass: bool) -> np.ndarray:
    rows, cols = shape
    center_row = rows // 2
    center_col = cols // 2
    y_grid, x_grid = np.ogrid[:rows, :cols]
    distance = np.sqrt((y_grid - center_row) ** 2 + (x_grid - center_col) ** 2)
    if high_pass:
        return (distance >= cutoff).astype(np.float64)
    return (distance <= cutoff).astype(np.float64)


def apply_low_pass_filter(image: np.ndarray, cutoff: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    frequency, _ = compute_frequency_spectrum(image)
    mask = _distance_mask(image.shape, cutoff, high_pass=False)
    filtered_frequency = frequency * mask
    reconstructed = np.fft.ifft2(np.fft.ifftshift(filtered_frequency))
    result = np.clip(np.round(np.abs(reconstructed)), 0, 255).astype(np.uint8)
    return mask, np.log1p(np.abs(filtered_frequency)), result


def apply_high_pass_filter(image: np.ndarray, cutoff: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    frequency, _ = compute_frequency_spectrum(image)
    mask = _distance_mask(image.shape, cutoff, high_pass=True)
    filtered_frequency = frequency * mask
    reconstructed = np.fft.ifft2(np.fft.ifftshift(filtered_frequency))
    result = np.clip(np.round(np.abs(reconstructed)), 0, 255).astype(np.uint8)
    return mask, np.log1p(np.abs(filtered_frequency)), result
