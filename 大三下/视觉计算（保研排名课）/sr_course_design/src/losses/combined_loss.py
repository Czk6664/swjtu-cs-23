"""Loss functions for super-resolution course project."""

from __future__ import annotations

import mindspore.nn as nn
import mindspore.ops as ops


class EdgeLoss(nn.Cell):
    """Simple edge-aware loss based on finite differences."""

    def __init__(self) -> None:
        super().__init__()
        self.abs = ops.Abs()

    def gradient_map(self, x):
        grad_h = x[:, :, 1:, :] - x[:, :, :-1, :]
        grad_w = x[:, :, :, 1:] - x[:, :, :, :-1]
        return self.abs(grad_h).mean() + self.abs(grad_w).mean()

    def construct(self, pred, target):
        return self.abs(self.gradient_map(pred) - self.gradient_map(target))


class LaplacianLoss(nn.Cell):
    """Second-order structure loss for high-frequency reconstruction."""

    def __init__(self) -> None:
        super().__init__()
        self.abs = ops.Abs()

    def laplacian_map(self, x):
        center = x[:, :, 1:-1, 1:-1]
        laplacian = (
            x[:, :, :-2, 1:-1]
            + x[:, :, 2:, 1:-1]
            + x[:, :, 1:-1, :-2]
            + x[:, :, 1:-1, 2:]
            - 4.0 * center
        )
        return laplacian

    def construct(self, pred, target):
        return self.abs(self.laplacian_map(pred) - self.laplacian_map(target)).mean()


class CombinedLoss(nn.Cell):
    """Combine pixel reconstruction loss and optional structure losses."""

    def __init__(
        self,
        use_edge_loss: bool = True,
        edge_weight: float = 0.05,
        use_laplacian_loss: bool = False,
        laplacian_weight: float = 0.01,
    ) -> None:
        super().__init__()
        self.pixel_loss = nn.L1Loss()
        self.use_edge_loss = use_edge_loss
        self.edge_weight = edge_weight
        self.edge_loss = EdgeLoss()
        self.use_laplacian_loss = use_laplacian_loss
        self.laplacian_weight = laplacian_weight
        self.laplacian_loss = LaplacianLoss()

    def construct(self, pred, target):
        total = self.pixel_loss(pred, target)
        if self.use_edge_loss:
            total = total + self.edge_weight * self.edge_loss(pred, target)
        if self.use_laplacian_loss:
            total = total + self.laplacian_weight * self.laplacian_loss(pred, target)
        return total
