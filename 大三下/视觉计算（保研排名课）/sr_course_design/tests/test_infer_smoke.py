import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.infer import run_inference


def test_bicubic_inference_saves_output(tmp_path: Path) -> None:
    input_dir = tmp_path / "inputs"
    output_dir = tmp_path / "outputs"
    input_dir.mkdir()
    output_dir.mkdir()

    image = np.random.randint(0, 256, size=(8, 8, 3), dtype=np.uint8)
    Image.fromarray(image).save(input_dir / "sample.png")

    run_inference(
        model_name="bicubic",
        scale=2,
        input_path=str(input_dir),
        output_path=str(output_dir),
        num_features=16,
    )

    result_path = output_dir / "sample.png"
    assert result_path.exists()
