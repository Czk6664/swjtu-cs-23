import sys
from pathlib import Path

import numpy as np
import pytest

ms = pytest.importorskip("mindspore")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from losses.combined_loss import CombinedLoss, LaplacianLoss


def test_laplacian_loss_is_zero_for_identical_tensors() -> None:
    loss = LaplacianLoss()
    tensor = ms.Tensor(np.random.rand(1, 3, 8, 8).astype(np.float32))

    value = float(loss(tensor, tensor).asnumpy())

    assert value == pytest.approx(0.0)


def test_combined_loss_accepts_laplacian_term() -> None:
    loss = CombinedLoss(use_edge_loss=False, use_laplacian_loss=True, laplacian_weight=0.01)
    pred = ms.Tensor(np.zeros((1, 3, 8, 8), dtype=np.float32))
    target = ms.Tensor(np.ones((1, 3, 8, 8), dtype=np.float32))

    value = float(loss(pred, target).asnumpy())

    assert value > 0.0
