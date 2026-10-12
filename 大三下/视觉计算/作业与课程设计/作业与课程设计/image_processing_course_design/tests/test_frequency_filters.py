import numpy as np

from frequency_filters import apply_high_pass_filter, apply_low_pass_filter


def test_low_pass_filter_keeps_shape() -> None:
    image = np.array(
        [[10, 20, 30, 40], [20, 30, 40, 50], [30, 40, 50, 60], [40, 50, 60, 70]],
        dtype=np.uint8,
    )

    mask, spectrum, result = apply_low_pass_filter(image, cutoff=1.5)

    assert mask.shape == image.shape
    assert spectrum.shape == image.shape
    assert result.shape == image.shape
    assert result.dtype == np.uint8


def test_high_pass_filter_keeps_shape() -> None:
    image = np.array(
        [[10, 20, 30, 40], [20, 30, 40, 50], [30, 40, 50, 60], [40, 50, 60, 70]],
        dtype=np.uint8,
    )

    mask, spectrum, result = apply_high_pass_filter(image, cutoff=1.5)

    assert mask.shape == image.shape
    assert spectrum.shape == image.shape
    assert result.shape == image.shape
    assert result.dtype == np.uint8
