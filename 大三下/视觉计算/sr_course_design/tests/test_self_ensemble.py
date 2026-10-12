import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.self_ensemble import ENSEMBLE_TRANSFORMS, apply_transform, invert_transform
from tools.run_self_ensemble_eval import run_self_ensemble


def test_self_ensemble_transforms_are_reversible() -> None:
    image = np.arange(5 * 7 * 3, dtype=np.float32).reshape(5, 7, 3)

    for transform in ENSEMBLE_TRANSFORMS:
        restored = invert_transform(apply_transform(image, transform), transform)
        assert restored.shape == image.shape
        np.testing.assert_array_equal(restored, image)


def test_bicubic_self_ensemble_writes_scaled_output(tmp_path: Path) -> None:
    input_dir = tmp_path / "inputs"
    output_dir = tmp_path / "outputs"
    input_dir.mkdir()
    image = np.random.randint(0, 256, size=(8, 10, 3), dtype=np.uint8)
    Image.fromarray(image).save(input_dir / "sample.png")

    run_self_ensemble(
        model_name="bicubic",
        scale=2,
        input_path=input_dir,
        output_path=output_dir,
        num_features=16,
    )

    result = Image.open(output_dir / "sample.png")
    assert result.size == (20, 16)
