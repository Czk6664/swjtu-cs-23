import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.datasets.sr_dataset import DatasetConfig, image_to_tensor, list_image_pairs, random_patch, tensor_to_image
from src.train import TrainConfig, SuperResolutionTrainer


def test_list_image_pairs_matches_filenames(tmp_path: Path) -> None:
    lr_dir = tmp_path / "LR"
    hr_dir = tmp_path / "HR"
    lr_dir.mkdir()
    hr_dir.mkdir()

    import PIL.Image

    image = np.random.randint(0, 256, size=(8, 8, 3), dtype=np.uint8)
    PIL.Image.fromarray(image).save(lr_dir / "a.png")
    PIL.Image.fromarray(image).save(hr_dir / "a.png")
    PIL.Image.fromarray(image).save(lr_dir / "b.png")

    pairs = list_image_pairs(DatasetConfig(root_dir=tmp_path))

    assert len(pairs) == 1
    assert pairs[0].lr_path.name == "a.png"
    assert pairs[0].hr_path.name == "a.png"


def test_random_patch_keeps_scale_alignment() -> None:
    lr_image = np.zeros((12, 12, 3), dtype=np.uint8)
    hr_image = np.zeros((24, 24, 3), dtype=np.uint8)

    lr_patch, hr_patch = random_patch(lr_image, hr_image, patch_size=6, scale=2)

    assert lr_patch.shape == (6, 6, 3)
    assert hr_patch.shape == (12, 12, 3)


def test_tensor_image_roundtrip_preserves_shape() -> None:
    image = np.random.randint(0, 256, size=(10, 8, 3), dtype=np.uint8)

    tensor = image_to_tensor(image)
    restored = tensor_to_image(tensor)

    assert tensor.shape == (3, 10, 8)
    assert restored.shape == image.shape


def test_trainer_creates_multiple_patches_per_image(tmp_path: Path) -> None:
    ms = pytest.importorskip("mindspore")
    lr_dir = tmp_path / "LR"
    hr_dir = tmp_path / "HR"
    lr_dir.mkdir()
    hr_dir.mkdir()

    import PIL.Image

    lr_image = np.random.randint(0, 256, size=(16, 16, 3), dtype=np.uint8)
    hr_image = np.random.randint(0, 256, size=(32, 32, 3), dtype=np.uint8)
    PIL.Image.fromarray(lr_image).save(lr_dir / "a.png")
    PIL.Image.fromarray(hr_image).save(hr_dir / "a.png")

    config = TrainConfig(
        model_name="srcnn",
        scale=2,
        batch_size=1,
        epochs=1,
        learning_rate=0.0002,
        patch_size=8,
        num_features=8,
        use_edge_loss=False,
        dataset_dir=str(tmp_path),
        eval_dir=str(tmp_path),
        checkpoint_dir=str(tmp_path / "checkpoints"),
        result_dir=str(tmp_path / "results"),
        log_csv_path=str(tmp_path / "logs" / "metrics.csv"),
        patches_per_image=3,
    )
    ms.set_context(mode=ms.PYNATIVE_MODE, device_target="CPU")
    trainer = SuperResolutionTrainer(config)

    samples = trainer.load_split(tmp_path)

    assert len(samples) == 3
