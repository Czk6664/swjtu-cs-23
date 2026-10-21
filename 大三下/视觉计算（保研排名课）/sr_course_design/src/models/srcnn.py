"""SRCNN baseline implemented with MindSpore."""

from __future__ import annotations

import mindspore.nn as nn
from mindspore import ops


class SRCNN(nn.Cell):
    """A simple SRCNN baseline for x2/x4 super-resolution."""

    def __init__(self, scale: int = 2) -> None:
        super().__init__()
        self.scale = scale
        self.resize = ops.ResizeBilinearV2()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=9, pad_mode="pad", padding=4)
        self.conv2 = nn.Conv2d(64, 32, kernel_size=5, pad_mode="pad", padding=2)
        self.conv3 = nn.Conv2d(32, 3, kernel_size=5, pad_mode="pad", padding=2)
        self.relu = nn.ReLU()

    def construct(self, x):
        target_size = (x.shape[2] * self.scale, x.shape[3] * self.scale)
        out = self.resize(x, target_size)
        out = self.relu(self.conv1(out))
        out = self.relu(self.conv2(out))
        return self.conv3(out)
