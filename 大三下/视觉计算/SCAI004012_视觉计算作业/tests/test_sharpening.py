import numpy as np

from sharpening import laplacian_sharpen, sobel_sharpen


def test_laplacian_sharpen_keeps_shape_dtype_and_range() -> None:
    image = np.array([[20, 20, 20], [20, 90, 20], [20, 20, 20]], dtype=np.uint8)

    response, result = laplacian_sharpen(image)

    assert response.shape == image.shape
    assert result.shape == image.shape
    assert result.dtype == np.uint8
    assert result.max() <= 255


def test_sobel_sharpen_detects_edge() -> None:
    image = np.array([[0, 0, 255], [0, 0, 255], [0, 0, 255]], dtype=np.uint8)

    response, result = sobel_sharpen(image)

    assert response.shape == image.shape
    assert result.shape == image.shape
    assert response.max() > 0
