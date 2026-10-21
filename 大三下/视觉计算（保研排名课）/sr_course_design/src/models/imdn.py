"""Lightweight IMDN-style super-resolution network for MindSpore."""

from __future__ import annotations

import mindspore.nn as nn
from mindspore import ops


class ConvBlock(nn.Cell):
    """Convolution followed by activation."""

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3) -> None:
        super().__init__()
        padding = kernel_size // 2
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, pad_mode="pad", padding=padding)
        self.act = nn.LeakyReLU(alpha=0.05)

    def construct(self, x):
        return self.act(self.conv(x))


class DistillationBlock(nn.Cell):
    """A simplified information distillation block."""

    def __init__(self, channels: int) -> None:
        super().__init__()
        self.conv1 = ConvBlock(channels, channels)
        self.conv2 = ConvBlock(channels, channels)
        self.conv3 = ConvBlock(channels, channels)
        self.fuse = nn.Conv2d(channels * 3, channels, kernel_size=1, pad_mode="valid")

    def construct(self, x):
        out1 = self.conv1(x)
        out2 = self.conv2(out1)
        out3 = self.conv3(out2)
        fused = ops.concat((out1, out2, out3), axis=1)
        return self.fuse(fused) + x


class InformationDistillationBlock(nn.Cell):
    """Split-and-fuse distillation block closer to the original IMDN idea."""

    def __init__(self, channels: int, distill_ratio: float = 0.25) -> None:
        super().__init__()
        self.distilled_channels = max(1, int(channels * distill_ratio))
        self.remaining_channels = channels - self.distilled_channels
        if self.remaining_channels <= 0:
            raise ValueError("channels must leave at least one remaining channel after distillation")

        self.conv1 = ConvBlock(channels, channels)
        self.conv2 = ConvBlock(self.remaining_channels, channels)
        self.conv3 = ConvBlock(self.remaining_channels, channels)
        self.conv4 = ConvBlock(self.remaining_channels, self.distilled_channels)
        self.fuse = nn.Conv2d(self.distilled_channels * 4, channels, kernel_size=1, pad_mode="valid")

    def split_features(self, x):
        distilled = x[:, : self.distilled_channels, :, :]
        remaining = x[:, self.distilled_channels :, :, :]
        return distilled, remaining

    def construct(self, x):
        out1 = self.conv1(x)
        distilled1, remaining1 = self.split_features(out1)

        out2 = self.conv2(remaining1)
        distilled2, remaining2 = self.split_features(out2)

        out3 = self.conv3(remaining2)
        distilled3, remaining3 = self.split_features(out3)

        distilled4 = self.conv4(remaining3)
        fused = ops.concat((distilled1, distilled2, distilled3, distilled4), axis=1)
        return self.fuse(fused) + x


class ChannelAttention(nn.Cell):
    """Lightweight SE-style channel attention for feature recalibration."""

    def __init__(self, channels: int, reduction: int = 4) -> None:
        super().__init__()
        hidden = max(1, channels // reduction)
        self.pool = ops.ReduceMean(keep_dims=True)
        self.squeeze = nn.Conv2d(channels, hidden, kernel_size=1, pad_mode="valid")
        self.act = nn.ReLU()
        self.excitation = nn.Conv2d(hidden, channels, kernel_size=1, pad_mode="valid")
        self.sigmoid = nn.Sigmoid()

    def construct(self, x):
        weights = self.pool(x, (2, 3))
        weights = self.squeeze(weights)
        weights = self.act(weights)
        weights = self.excitation(weights)
        weights = self.sigmoid(weights)
        return x * weights


class AttentionDistillationBlock(nn.Cell):
    """Distillation block followed by channel attention."""

    def __init__(self, channels: int, reduction: int = 4) -> None:
        super().__init__()
        self.distill = DistillationBlock(channels)
        self.attention = ChannelAttention(channels, reduction=reduction)

    def construct(self, x):
        refined = self.distill(x)
        return self.attention(refined) + x


class PixelShuffleBlock(nn.Cell):
    """Upsampling block based on depth-to-space."""

    def __init__(self, channels: int, scale: int) -> None:
        super().__init__()
        self.conv = nn.Conv2d(channels, channels * scale * scale, kernel_size=3, pad_mode="pad", padding=1)
        self.shuffle = ops.DepthToSpace(scale)

    def construct(self, x):
        return self.shuffle(self.conv(x))


class IMDN(nn.Cell):
    """A lightweight IMDN-style network for course design use."""

    def __init__(self, scale: int = 2, num_features: int = 32, num_blocks: int = 4) -> None:
        super().__init__()
        self.head = nn.Conv2d(3, num_features, kernel_size=3, pad_mode="pad", padding=1)
        self.blocks = nn.SequentialCell([DistillationBlock(num_features) for _ in range(num_blocks)])
        self.fusion = nn.Conv2d(num_features, num_features, kernel_size=3, pad_mode="pad", padding=1)
        self.upsample = PixelShuffleBlock(num_features, scale)
        self.tail = nn.Conv2d(num_features, 3, kernel_size=3, pad_mode="pad", padding=1)

    def construct(self, x):
        features = self.head(x)
        refined = self.blocks(features)
        fused = self.fusion(refined) + features
        upsampled = self.upsample(fused)
        return self.tail(upsampled)


class IDBIMDN(nn.Cell):
    """IMDN variant with split-and-fuse information distillation blocks."""

    def __init__(
        self,
        scale: int = 2,
        num_features: int = 32,
        num_blocks: int = 4,
        distill_ratio: float = 0.25,
    ) -> None:
        super().__init__()
        self.head = nn.Conv2d(3, num_features, kernel_size=3, pad_mode="pad", padding=1)
        self.blocks = nn.SequentialCell(
            [InformationDistillationBlock(num_features, distill_ratio=distill_ratio) for _ in range(num_blocks)]
        )
        self.fusion = nn.Conv2d(num_features, num_features, kernel_size=3, pad_mode="pad", padding=1)
        self.upsample = PixelShuffleBlock(num_features, scale)
        self.tail = nn.Conv2d(num_features, 3, kernel_size=3, pad_mode="pad", padding=1)

    def construct(self, x):
        features = self.head(x)
        refined = self.blocks(features)
        fused = self.fusion(refined) + features
        upsampled = self.upsample(fused)
        return self.tail(upsampled)


class CAIMDN(nn.Cell):
    """Channel-attention enhanced IMDN variant for ablation experiments."""

    def __init__(
        self,
        scale: int = 2,
        num_features: int = 32,
        num_blocks: int = 4,
        attention_reduction: int = 4,
    ) -> None:
        super().__init__()
        self.head = nn.Conv2d(3, num_features, kernel_size=3, pad_mode="pad", padding=1)
        self.blocks = nn.SequentialCell(
            [AttentionDistillationBlock(num_features, reduction=attention_reduction) for _ in range(num_blocks)]
        )
        self.fusion = nn.Conv2d(num_features, num_features, kernel_size=3, pad_mode="pad", padding=1)
        self.upsample = PixelShuffleBlock(num_features, scale)
        self.tail = nn.Conv2d(num_features, 3, kernel_size=3, pad_mode="pad", padding=1)

    def construct(self, x):
        features = self.head(x)
        refined = self.blocks(features)
        fused = self.fusion(refined) + features
        upsampled = self.upsample(fused)
        return self.tail(upsampled)
