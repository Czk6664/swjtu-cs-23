from __future__ import annotations

import torch
import torch.nn as nn

from ultralytics.nn.modules import CBAM


def patch_ultralytics() -> None:
    """Inject AutoCBAM into the Ultralytics yaml parser globals.

    Call this **before** loading any model yaml that uses ``AutoCBAM``.
    """
    import ultralytics.nn.tasks as tasks

    tasks.AutoCBAM = AutoCBAM


class AutoCBAM(nn.Module):
    """CBAM wrapper that auto-detects input channels on first forward pass.

    This solves the problem that CBAM requires an explicit ``c1`` argument,
    but the Ultralytics yaml parser does not auto-scale channel values for
    modules outside ``base_modules``.  With ``AutoCBAM`` you can write
    ``[-1, 1, AutoCBAM, []]`` in any model yaml regardless of scale.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._initialized = False
        self._kernel_size = kwargs.get("kernel_size", 7)
        self.cbam: CBAM | None = None

    def _initialize(self, x: torch.Tensor) -> None:
        c1 = x.shape[1]
        self.cbam = CBAM(c1, self._kernel_size).to(x.device).to(x.dtype)
        self._initialized = True

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if not self._initialized:
            self._initialize(x)
        return self.cbam(x)
