import numpy as np

from frequency_filters import apply_high_pass_filter, apply_low_pass_filter, circular_frequency_mask


def test_low_pass_filter_keeps_shape_dtype_and_range() -> None:
    image = np.array(
        [[10, 20, 30, 40], [20, 30, 40, 50], [30, 40, 50, 60], [40, 50, 60, 70]],
        dtype=np.uint8,
    )

    mask, spectrum, result = apply_low_pass_filter(image, cutoff=1.5)

    assert mask.shape == image.shape
    assert spectrum.shape == image.shape
    assert result.shape == image.shape
    assert result.dtype == np.uint8
    assert result.min() >= 0
    assert result.max() <= 255


def test_high_pass_filter_keeps_shape_dtype_and_range() -> None:
    image = np.array(
        [[10, 20, 30, 40], [20, 30, 40, 50], [30, 40, 50, 60], [40, 50, 60, 70]],
        dtype=np.uint8,
    )

    mask, spectrum, result = apply_high_pass_filter(image, cutoff=1.5)

    assert mask.shape == image.shape
    assert spectrum.shape == image.shape
    assert result.shape == image.shape
    assert result.dtype == np.uint8
    assert result.min() >= 0
    assert result.max() <= 255


def test_frequency_masks_are_complementary_except_boundary_rule() -> None:
    low = circular_frequency_mask((7, 7), cutoff=2, mode="low")
    high = circular_frequency_mask((7, 7), cutoff=2, mode="high")

    assert low[3, 3] == 1
    assert high[3, 3] == 0
    assert low[0, 0] == 0
    assert high[0, 0] == 1
