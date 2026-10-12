from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from frequency_filters import apply_high_pass_filter, apply_low_pass_filter
from histogram_ops import histogram_equalization
from io_utils import (
    ensure_dir,
    load_image,
    normalize_to_uint8,
    save_comparison_grid,
    save_four_panel,
    save_histogram_pair,
    save_image,
)
from sharpening import laplacian_sharpen, sobel_gradient, sobel_sharpen
from spatial_filters import linear_smoothing_filter, order_statistic_filter


def _base_grid(size: int = 512) -> tuple[np.ndarray, np.ndarray]:
    y, x = np.mgrid[0:size, 0:size]
    return x.astype(np.float64), y.astype(np.float64)


def _draw_disk(image: np.ndarray, center: tuple[int, int], radius: int, value: float) -> None:
    x, y = _base_grid(image.shape[0])
    mask = (x - center[0]) ** 2 + (y - center[1]) ** 2 <= radius**2
    image[mask] = value


def generate_demo_images(raw_dir: Path) -> None:
    """Create deterministic complex grayscale images for reproducible experiments."""
    ensure_dir(raw_dir)
    rng = np.random.default_rng(20260429)
    size = 512
    x, y = _base_grid(size)

    low_contrast = 118 + 18 * np.sin(x / 38.0) + 12 * np.cos(y / 49.0)
    low_contrast += 8 * np.sin((x + y) / 67.0)
    _draw_disk(low_contrast, (155, 160), 72, 150)
    _draw_disk(low_contrast, (365, 330), 92, 92)
    low_contrast += rng.normal(0, 3.5, (size, size))
    save_image(raw_dir / "low_contrast_scene.png", low_contrast)

    texture = 120 + 50 * np.sin(x / 12.0) * np.cos(y / 17.0)
    texture += 28 * np.sin((x + 2 * y) / 19.0)
    texture += rng.normal(0, 8, (size, size))
    impulse = rng.random((size, size))
    texture[impulse < 0.035] = 0
    texture[impulse > 0.965] = 255
    save_image(raw_dir / "salt_pepper_texture.png", texture)

    edge_blocks = np.full((size, size), 70.0)
    edge_blocks[:, 190:205] = 225
    edge_blocks[205:220, :] = 210
    edge_blocks[70:210, 60:180] = 150
    edge_blocks[270:430, 80:250] = 35
    edge_blocks[95:260, 310:455] = 190
    _draw_disk(edge_blocks, (335, 360), 68, 245)
    edge_blocks += 18 * np.sin(x / 9.0)
    save_image(raw_dir / "edge_blocks.png", edge_blocks)

    frequency_pattern = 118 + 42 * np.sin(2 * np.pi * x / 18.0)
    frequency_pattern += 30 * np.sin(2 * np.pi * y / 37.0)
    frequency_pattern += 22 * np.sin(2 * np.pi * (x + y) / 80.0)
    checker = ((x // 24 + y // 24) % 2) * 34
    frequency_pattern += checker
    save_image(raw_dir / "frequency_pattern.png", frequency_pattern)


def image_gradient_mean(image: np.ndarray) -> float:
    return float(sobel_gradient(image).mean())


def high_frequency_ratio(image: np.ndarray, cutoff: float = 28.0) -> float:
    frequency = np.fft.fftshift(np.fft.fft2(image.astype(np.float64)))
    rows, cols = image.shape
    y_grid, x_grid = np.ogrid[:rows, :cols]
    distance = np.sqrt((y_grid - rows // 2) ** 2 + (x_grid - cols // 2) ** 2)
    total_energy = np.sum(np.abs(frequency) ** 2)
    high_energy = np.sum(np.abs(frequency[distance >= cutoff]) ** 2)
    return float(high_energy / total_energy)


def process_image(image_path: Path, output_root: Path, figures_dir: Path) -> dict[str, float | str]:
    image = load_image(image_path, grayscale=True)
    stem = image_path.stem

    histogram_dir = ensure_dir(output_root / "histogram")
    spatial_dir = ensure_dir(output_root / "spatial")
    sharpening_dir = ensure_dir(output_root / "sharpening")
    frequency_dir = ensure_dir(output_root / "frequency")

    equalized = histogram_equalization(image)
    save_image(histogram_dir / f"{stem}_equalized.png", equalized)
    save_histogram_pair(histogram_dir / f"{stem}_histograms.png", image, equalized)
    save_comparison_grid(figures_dir / f"{stem}_histogram_compare.png", [image, equalized], ["Original", "Equalized"])

    mean_result = linear_smoothing_filter(image, kernel_size=3)
    median_result = order_statistic_filter(image, kernel_size=3, mode="median")
    save_image(spatial_dir / f"{stem}_mean.png", mean_result)
    save_image(spatial_dir / f"{stem}_median.png", median_result)
    save_comparison_grid(
        figures_dir / f"{stem}_spatial_compare.png",
        [image, mean_result, median_result],
        ["Original", "Mean 3x3", "Median 3x3"],
    )

    laplacian_response, laplacian_result = laplacian_sharpen(image, alpha=1.0)
    sobel_response, sobel_result = sobel_sharpen(image, alpha=0.6)
    save_image(sharpening_dir / f"{stem}_laplacian_response.png", laplacian_response)
    save_image(sharpening_dir / f"{stem}_laplacian_sharpened.png", laplacian_result)
    save_image(sharpening_dir / f"{stem}_sobel_response.png", sobel_response)
    save_image(sharpening_dir / f"{stem}_sobel_sharpened.png", sobel_result)
    save_comparison_grid(
        figures_dir / f"{stem}_sharpen_compare.png",
        [image, laplacian_result, sobel_result],
        ["Original", "Laplacian", "Sobel"],
    )

    low_mask, low_spectrum, low_result = apply_low_pass_filter(image, cutoff=28.0)
    high_mask, high_spectrum, high_result = apply_high_pass_filter(image, cutoff=28.0)
    save_image(frequency_dir / f"{stem}_low_pass.png", low_result)
    save_image(frequency_dir / f"{stem}_high_pass.png", high_result)
    save_image(frequency_dir / f"{stem}_low_mask.png", normalize_to_uint8(low_mask))
    save_image(frequency_dir / f"{stem}_high_mask.png", normalize_to_uint8(high_mask))
    save_image(frequency_dir / f"{stem}_low_spectrum.png", normalize_to_uint8(low_spectrum))
    save_image(frequency_dir / f"{stem}_high_spectrum.png", normalize_to_uint8(high_spectrum))
    save_comparison_grid(
        figures_dir / f"{stem}_frequency_compare.png",
        [image, low_result, high_result],
        ["Original", "FFT Low-pass", "FFT High-pass"],
    )
    save_four_panel(
        figures_dir / f"{stem}_frequency_detail.png",
        [normalize_to_uint8(low_mask), normalize_to_uint8(low_spectrum), normalize_to_uint8(high_mask), normalize_to_uint8(high_spectrum)],
        ["Low-pass mask", "Low-pass spectrum", "High-pass mask", "High-pass spectrum"],
    )

    return {
        "image": stem,
        "std_original": float(image.std()),
        "std_equalized": float(equalized.std()),
        "impulse_pixels_original": float(np.count_nonzero((image == 0) | (image == 255))),
        "impulse_pixels_mean": float(np.count_nonzero((mean_result == 0) | (mean_result == 255))),
        "impulse_pixels_median": float(np.count_nonzero((median_result == 0) | (median_result == 255))),
        "gradient_original": image_gradient_mean(image),
        "gradient_laplacian": image_gradient_mean(laplacian_result),
        "gradient_sobel": image_gradient_mean(sobel_result),
        "high_frequency_ratio_original": high_frequency_ratio(image),
        "high_frequency_ratio_low_pass": high_frequency_ratio(low_result),
        "high_frequency_ratio_high_pass": high_frequency_ratio(high_result),
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    raw_dir = project_root / "data" / "raw"
    processed_dir = ensure_dir(project_root / "data" / "processed")
    figures_dir = ensure_dir(project_root / "report" / "figures")

    generate_demo_images(raw_dir)
    image_paths = sorted(raw_dir.glob("*.png"))
    metrics = [process_image(image_path, processed_dir, figures_dir) for image_path in image_paths]

    metrics_path = project_root / "report" / "analysis_metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Processed {len(image_paths)} images.")
    print(f"Figures: {figures_dir}")
    print(f"Metrics: {metrics_path}")


if __name__ == "__main__":
    main()
