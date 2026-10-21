from __future__ import annotations

from pathlib import Path

import numpy as np

from frequency_filters import apply_high_pass_filter, apply_low_pass_filter
from histogram_ops import histogram_equalization
from io_utils import ensure_dir, load_image, normalize_to_uint8, save_comparison_grid, save_histogram_plot, save_image
from sharpening import laplacian_sharpen, sobel_sharpen
from spatial_filters import mean_filter, order_statistic_filter


def process_image(image_path: Path, output_root: Path) -> None:
    image = load_image(image_path, grayscale=True)
    stem = image_path.stem

    histogram_dir = ensure_dir(output_root / 'histogram')
    spatial_dir = ensure_dir(output_root / 'spatial')
    sharpening_dir = ensure_dir(output_root / 'sharpening')
    frequency_dir = ensure_dir(output_root / 'frequency')
    figures_dir = ensure_dir(output_root / 'figures')

    equalized = histogram_equalization(image)
    save_image(histogram_dir / f'{stem}_equalized.png', equalized)
    save_histogram_plot(histogram_dir / f'{stem}_original_hist.png', image, f'{stem} original histogram')
    save_histogram_plot(histogram_dir / f'{stem}_equalized_hist.png', equalized, f'{stem} equalized histogram')
    save_comparison_grid(figures_dir / f'{stem}_histogram_compare.png', [image, equalized], ['Original', 'Equalized'])

    mean_result = mean_filter(image, kernel_size=3)
    median_result = order_statistic_filter(image, kernel_size=3, mode='median')
    save_image(spatial_dir / f'{stem}_mean.png', mean_result)
    save_image(spatial_dir / f'{stem}_median.png', median_result)
    save_comparison_grid(figures_dir / f'{stem}_spatial_compare.png', [image, mean_result, median_result], ['Original', 'Mean', 'Median'])

    laplacian_response, laplacian_result = laplacian_sharpen(image)
    sobel_response, sobel_result = sobel_sharpen(image)
    save_image(sharpening_dir / f'{stem}_laplacian_response.png', laplacian_response)
    save_image(sharpening_dir / f'{stem}_laplacian_sharpened.png', laplacian_result)
    save_image(sharpening_dir / f'{stem}_sobel_response.png', sobel_response)
    save_image(sharpening_dir / f'{stem}_sobel_sharpened.png', sobel_result)
    save_comparison_grid(figures_dir / f'{stem}_sharpen_compare.png', [image, laplacian_result, sobel_result], ['Original', 'Laplacian', 'Sobel'])

    low_mask, low_spectrum, low_result = apply_low_pass_filter(image, cutoff=20)
    high_mask, high_spectrum, high_result = apply_high_pass_filter(image, cutoff=20)
    save_image(frequency_dir / f'{stem}_low_pass.png', low_result)
    save_image(frequency_dir / f'{stem}_high_pass.png', high_result)
    save_image(frequency_dir / f'{stem}_low_mask.png', normalize_to_uint8(low_mask * 255.0))
    save_image(frequency_dir / f'{stem}_high_mask.png', normalize_to_uint8(high_mask * 255.0))
    save_image(frequency_dir / f'{stem}_low_spectrum.png', normalize_to_uint8(low_spectrum))
    save_image(frequency_dir / f'{stem}_high_spectrum.png', normalize_to_uint8(high_spectrum))
    save_comparison_grid(figures_dir / f'{stem}_frequency_compare.png', [image, low_result, high_result], ['Original', 'Low-pass', 'High-pass'])


if __name__ == '__main__':
    project_root = Path(__file__).resolve().parents[1]
    input_dir = project_root / 'data' / 'raw'
    output_dir = ensure_dir(project_root / 'data' / 'processed')

    image_paths = sorted([*input_dir.glob('*.png'), *input_dir.glob('*.jpg'), *input_dir.glob('*.jpeg')])
    if not image_paths:
        raise SystemExit('No input images found in data/raw')

    for image_path in image_paths:
        process_image(image_path, output_dir)

    print(f'Processed {len(image_paths)} images into {output_dir}')
