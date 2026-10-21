import numpy as np

from spatial_filters import linear_smoothing_filter, order_statistic_filter


def test_linear_smoothing_filter_keeps_shape() -> None:
    image = np.array([[10, 20, 30], [40, 50, 60], [70, 80, 90]], dtype=np.uint8)

    result = linear_smoothing_filter(image, kernel_size=3)

    assert result.shape == image.shape
    assert result.dtype == np.uint8


def test_median_filter_removes_center_impulse() -> None:
    image = np.array([[10, 10, 10], [10, 255, 10], [10, 10, 10]], dtype=np.uint8)

    result = order_statistic_filter(image, kernel_size=3, mode="median")

    assert result[1, 1] == 10
