import numpy as np

from sharpening import laplacian_sharpen, sobel_sharpen


def test_laplacian_sharpen_keeps_shape() -> None:
    image = np.array([[10, 20, 30], [40, 50, 60], [70, 80, 90]], dtype=np.uint8)

    response, result = laplacian_sharpen(image)

    assert response.shape == image.shape
    assert result.shape == image.shape
    assert result.dtype == np.uint8


def test_sobel_detects_edge() -> None:
    image = np.array([[0, 0, 0], [0, 255, 255], [0, 255, 255]], dtype=np.uint8)

    response, _ = sobel_sharpen(image)

    assert response.max() > 0
