"""Generate real IMDN intermediate feature-response visualization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import mindspore as ms
import numpy as np
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.datasets.sr_dataset import image_to_tensor
from src.models.imdn import IMDN


DEFAULT_INPUT = PROJECT_ROOT / "data" / "eval" / "LR" / "0821.png"
DEFAULT_CHECKPOINT = PROJECT_ROOT / "checkpoints" / "imdn_no_edge_x2.ckpt"
DEFAULT_OUTPUT = PROJECT_ROOT / "report" / "figures" / "imdn_feature_maps.png"


def normalize_map(feature: np.ndarray) -> np.ndarray:
    """Convert one feature map to uint8 grayscale."""

    feature = feature.astype(np.float32)
    feature = feature - float(feature.min())
    max_value = float(feature.max())
    if max_value > 1e-8:
        feature = feature / max_value
    return np.clip(feature * 255.0, 0, 255).astype(np.uint8)


def make_tile(array: np.ndarray, size: int, label: str) -> Image.Image:
    """Render one normalized map tile with a small label."""

    image = Image.fromarray(array).convert("L").resize((size, size), Image.BICUBIC).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, size - 1, 22), fill="white")
    draw.text((6, 5), label, fill="black")
    return image


def rgb_input_tiles(image: Image.Image, size: int) -> list[Image.Image]:
    """Create four input-reference tiles from the LR image."""

    rgb = np.array(image.convert("RGB"), dtype=np.uint8)
    channels = [
        ("LR gray", np.mean(rgb, axis=2).astype(np.uint8)),
        ("LR R", rgb[:, :, 0]),
        ("LR G", rgb[:, :, 1]),
        ("LR B", rgb[:, :, 2]),
    ]
    return [make_tile(values, size, label) for label, values in channels]


def feature_tiles(name: str, tensor: ms.Tensor, size: int, channels: int = 4) -> list[Image.Image]:
    """Create tiles for selected channels from a BCHW feature tensor."""

    features = tensor.asnumpy()[0]
    tiles: list[Image.Image] = []
    for index in range(min(channels, features.shape[0])):
        label = f"{name} c{index + 1}"
        tiles.append(make_tile(normalize_map(features[index]), size, label))
    return tiles


def build_canvas(rows: list[list[Image.Image]], output_path: Path) -> None:
    """Compose feature tiles into one paper-friendly grid."""

    tile_size = rows[0][0].width
    row_label_width = 132
    gap = 12
    margin = 18
    title_height = 34
    row_names = ["Input", "Head", "Block", "Fusion"]

    width = margin * 2 + row_label_width + len(rows[0]) * tile_size + (len(rows[0]) - 1) * gap
    height = margin * 2 + title_height + len(rows) * tile_size + (len(rows) - 1) * gap
    canvas = Image.new("RGB", (width, height), color=(245, 243, 238))
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, margin), "Real IMDN intermediate feature responses from validation sample 0821.png", fill="black")

    y = margin + title_height
    for row_name, row in zip(row_names, rows):
        draw.text((margin, y + tile_size // 2 - 8), row_name, fill="black")
        x = margin + row_label_width
        for tile in row:
            canvas.paste(tile, (x, y))
            x += tile_size + gap
        y += tile_size + gap

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def generate_feature_maps(input_path: Path, checkpoint_path: Path, output_path: Path, tile_size: int) -> None:
    """Run one IMDN forward pass and save intermediate feature maps."""

    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    ms.set_context(mode=ms.PYNATIVE_MODE, device_target="CPU")
    model = IMDN(scale=2, num_features=32)
    params = ms.load_checkpoint(str(checkpoint_path))
    ms.load_param_into_net(model, params)
    model.set_train(False)

    image = Image.open(input_path).convert("RGB")
    tensor = ms.Tensor(np.expand_dims(image_to_tensor(np.array(image, dtype=np.uint8)), axis=0))

    head = model.head(tensor)
    block = model.blocks(head)
    fusion = model.fusion(block) + head

    rows = [
        rgb_input_tiles(image, tile_size),
        feature_tiles("head", head, tile_size),
        feature_tiles("block", block, tile_size),
        feature_tiles("fusion", fusion, tile_size),
    ]
    build_canvas(rows, output_path)
    print(f"Saved feature map visualization: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate real IMDN feature map visualization")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tile-size", type=int, default=120)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_feature_maps(
        input_path=args.input,
        checkpoint_path=args.checkpoint,
        output_path=args.output,
        tile_size=args.tile_size,
    )


if __name__ == "__main__":
    main()
