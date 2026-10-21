"""MindSpore forward smoke test for super-resolution project."""

from __future__ import annotations

import mindspore as ms
import numpy as np

from src.models.imdn import IMDN
from src.models.srcnn import SRCNN


def describe_model(name: str, model) -> None:
    """Run a random tensor through a model and print tensor shapes."""

    fake_input = ms.Tensor(np.random.rand(1, 3, 16, 16).astype(np.float32))
    fake_output = model(fake_input)
    print(f"{name}: input={fake_input.shape}, output={fake_output.shape}")


def main() -> None:
    """Validate that MindSpore models can build and run forward."""

    ms.set_context(mode=ms.PYNATIVE_MODE)
    describe_model("SRCNN", SRCNN(scale=2))
    describe_model("IMDN", IMDN(scale=2, num_features=32))


if __name__ == "__main__":
    main()
