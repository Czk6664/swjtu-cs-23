import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from eval import calculate_psnr, calculate_ssim


def test_metrics_are_perfect_for_identical_images() -> None:
    image = np.full((16, 16, 3), 128, dtype=np.uint8)

    psnr_value = calculate_psnr(image, image)
    ssim_value = calculate_ssim(image, image)

    assert psnr_value == float("inf")
    assert abs(ssim_value - 1.0) < 1e-6


def test_metrics_drop_for_different_images() -> None:
    image_a = np.zeros((16, 16, 3), dtype=np.uint8)
    image_b = np.full((16, 16, 3), 255, dtype=np.uint8)

    psnr_value = calculate_psnr(image_a, image_b)
    ssim_value = calculate_ssim(image_a, image_b)

    assert psnr_value < 1.0
    assert ssim_value < 0.1
