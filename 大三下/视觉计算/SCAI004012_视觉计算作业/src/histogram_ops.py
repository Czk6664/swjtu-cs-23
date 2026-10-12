from __future__ import annotations

import numpy as np


def compute_histogram(image: np.ndarray) -> np.ndarray:
    """Return a 256-bin histogram for an 8-bit grayscale image."""
    if image.ndim != 2:
        raise ValueError("compute_histogram expects a grayscale image")
    histogram, _ = np.histogram(image.ravel(), bins=256, range=(0, 256))
    return histogram


def histogram_equalization(image: np.ndarray) -> np.ndarray:
    """Apply global histogram equalization to an 8-bit grayscale image."""
    if image.ndim != 2:
        raise ValueError("histogram_equalization expects a grayscale image")

    histogram = compute_histogram(image)
    cdf = histogram.cumsum()
    nonzero_cdf = cdf[cdf > 0]
    if nonzero_cdf.size == 0:
        return image.copy()

    cdf_min = nonzero_cdf[0]
    denominator = image.size - cdf_min
    if denominator <= 0:
        return image.copy()

    mapping = np.round((cdf - cdf_min) / denominator * 255.0)
    mapping = np.clip(mapping, 0, 255).astype(np.uint8)
    return mapping[image]
