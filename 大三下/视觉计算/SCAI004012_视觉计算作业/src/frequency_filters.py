from __future__ import annotations

import numpy as np


def compute_frequency_spectrum(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return centered FFT coefficients and log-magnitude spectrum."""
    if image.ndim != 2:
        raise ValueError("compute_frequency_spectrum expects a grayscale image")
    frequency = np.fft.fftshift(np.fft.fft2(image.astype(np.float64)))
    spectrum = np.log1p(np.abs(frequency))
    return frequency, spectrum


def circular_frequency_mask(shape: tuple[int, int], cutoff: float, mode: str) -> np.ndarray:
    """Build an ideal circular low-pass or high-pass mask."""
    if cutoff <= 0:
        raise ValueError("cutoff must be positive")
    if mode not in {"low", "high"}:
        raise ValueError("mode must be 'low' or 'high'")

    rows, cols = shape
    center_row = rows // 2
    center_col = cols // 2
    y_grid, x_grid = np.ogrid[:rows, :cols]
    distance = np.sqrt((y_grid - center_row) ** 2 + (x_grid - center_col) ** 2)
    if mode == "low":
        return (distance <= cutoff).astype(np.float64)
    return (distance >= cutoff).astype(np.float64)


def apply_frequency_filter(image: np.ndarray, cutoff: float, mode: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Filter a grayscale image in the Fourier domain."""
    frequency, _ = compute_frequency_spectrum(image)
    mask = circular_frequency_mask(image.shape, cutoff=cutoff, mode=mode)
    filtered_frequency = frequency * mask
    reconstructed = np.fft.ifft2(np.fft.ifftshift(filtered_frequency))

    if mode == "low":
        result = np.clip(np.round(np.real(reconstructed)), 0, 255).astype(np.uint8)
    else:
        high_component = np.abs(np.real(reconstructed))
        if high_component.max() > 0:
            high_component = high_component / high_component.max() * 255.0
        result = np.clip(np.round(high_component), 0, 255).astype(np.uint8)

    filtered_spectrum = np.log1p(np.abs(filtered_frequency))
    return mask, filtered_spectrum, result


def apply_low_pass_filter(image: np.ndarray, cutoff: float = 28.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return apply_frequency_filter(image, cutoff=cutoff, mode="low")


def apply_high_pass_filter(image: np.ndarray, cutoff: float = 28.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return apply_frequency_filter(image, cutoff=cutoff, mode="high")
