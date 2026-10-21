# CA-IMDN Improvement Video Design

## Goal

Create a short, PPT-ready video that only explains the added improvement in the improved model: channel attention after feature distillation.

## Audience

Visual computing course presentation audience. The explanation should stay shallow enough for listeners who know pixels and convolution but may not know attention modules.

## Style

- Academic, clean, SWJTU-inspired blue accent.
- Light background for PowerPoint readability.
- Calculations shown as visible matrices, vectors, arrows, and multiplication, not as text-only blocks.
- Slow animation pacing so the presenter can narrate each operation.

## Story

1. The distillation block outputs feature channels.
2. Global Average Pooling compresses each channel from H times W pixels into one scalar.
3. A small MLP-style attention branch maps 32 channels to 8 and back to 32.
4. Sigmoid turns those values into weights from 0 to 1.
5. Each channel is multiplied by its own weight, so useful texture channels stay bright and weak/noisy channels fade.
6. The residual connection adds the original feature back: Attention(Distill(F)) + F.
