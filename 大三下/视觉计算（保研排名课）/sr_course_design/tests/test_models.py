import sys
from pathlib import Path

import numpy as np
import pytest

ms = pytest.importorskip("mindspore")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.imdn import CAIMDN, IDBIMDN, IMDN
from models.srcnn import SRCNN


def test_srcnn_output_shape() -> None:
    model = SRCNN(scale=2)
    input_tensor = ms.Tensor(np.random.rand(1, 3, 8, 8).astype(np.float32))

    output = model(input_tensor)

    assert tuple(output.shape) == (1, 3, 16, 16)


def test_imdn_output_shape() -> None:
    model = IMDN(scale=2, num_features=16, num_blocks=2)
    input_tensor = ms.Tensor(np.random.rand(1, 3, 8, 8).astype(np.float32))

    output = model(input_tensor)

    assert tuple(output.shape) == (1, 3, 16, 16)


def test_ca_imdn_output_shape() -> None:
    model = CAIMDN(scale=2, num_features=16, num_blocks=2)
    input_tensor = ms.Tensor(np.random.rand(1, 3, 8, 8).astype(np.float32))

    output = model(input_tensor)

    assert tuple(output.shape) == (1, 3, 16, 16)


def test_idb_imdn_output_shape() -> None:
    model = IDBIMDN(scale=2, num_features=16, num_blocks=2)
    input_tensor = ms.Tensor(np.random.rand(1, 3, 8, 8).astype(np.float32))

    output = model(input_tensor)

    assert tuple(output.shape) == (1, 3, 16, 16)


def test_idb_imdn_has_trainable_parameters() -> None:
    model = IDBIMDN(scale=2, num_features=16, num_blocks=2)
    total = 0
    for parameter in model.trainable_params():
        size = 1
        for dim in parameter.shape:
            size *= dim
        total += size

    assert total > 0
