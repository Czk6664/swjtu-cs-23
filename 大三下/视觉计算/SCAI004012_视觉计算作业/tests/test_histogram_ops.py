import numpy as np

from histogram_ops import compute_histogram, histogram_equalization


def test_compute_histogram_counts_pixels() -> None:
    image = np.array([[0, 0, 1], [2, 2, 2]], dtype=np.uint8)

    histogram = compute_histogram(image)

    assert histogram[0] == 2
    assert histogram[1] == 1
    assert histogram[2] == 3
    assert histogram.sum() == image.size


def test_histogram_equalization_keeps_shape_dtype_and_range() -> None:
    image = np.array([[10, 10, 20], [30, 40, 40]], dtype=np.uint8)

    result = histogram_equalization(image)

    assert result.shape == image.shape
    assert result.dtype == np.uint8
    assert result.min() >= 0
    assert result.max() <= 255
