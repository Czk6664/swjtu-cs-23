"""Inference entrypoint for lightweight super-resolution project."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from src.datasets.sr_dataset import image_to_tensor, save_image, tensor_to_image


def load_mindspore():
    """Import MindSpore only when learned models are used."""

    import mindspore as ms

    return ms


def build_model(model_name: str, scale: int, num_features: int, num_blocks: int = 4):
    """Construct model from name."""

    normalized_name = model_name.lower()
    if normalized_name == "bicubic":
        return None
    if normalized_name == "srcnn":
        from src.models.srcnn import SRCNN

        return SRCNN(scale=scale)
    if normalized_name == "imdn":
        from src.models.imdn import IMDN

        return IMDN(scale=scale, num_features=num_features, num_blocks=num_blocks)
    if normalized_name == "ca_imdn":
        from src.models.imdn import CAIMDN

        return CAIMDN(scale=scale, num_features=num_features, num_blocks=num_blocks)
    if normalized_name == "idb_imdn":
        from src.models.imdn import IDBIMDN

        return IDBIMDN(scale=scale, num_features=num_features, num_blocks=num_blocks)
    raise ValueError(f"Unsupported model name: {model_name}")


def load_checkpoint_if_available(model, checkpoint_path: str | None) -> bool:
    """Load a MindSpore checkpoint into the model when a path is provided."""

    if not checkpoint_path:
        return False

    checkpoint_file = Path(checkpoint_path)
    if not checkpoint_file.exists():
        raise FileNotFoundError(f"Checkpoint file does not exist: {checkpoint_file}")

    ms = load_mindspore()
    param_dict = ms.load_checkpoint(str(checkpoint_file))
    ms.load_param_into_net(model, param_dict)
    return True


def bicubic_upscale(image: np.ndarray, scale: int) -> np.ndarray:
    """Upscale an image with bicubic interpolation."""

    pil_image = Image.fromarray(image)
    resized = pil_image.resize((image.shape[1] * scale, image.shape[0] * scale), Image.BICUBIC)
    return np.array(resized, dtype=np.uint8)


def collect_inputs(input_path: str | Path) -> list[Path]:
    """Collect one image path or all image files in a directory."""

    resolved_input = Path(input_path)
    if resolved_input.is_file():
        return [resolved_input]
    if resolved_input.is_dir():
        return sorted(path for path in resolved_input.iterdir() if path.is_file())
    raise FileNotFoundError(f"Input path does not exist: {resolved_input}")


def run_inference(
    model_name: str,
    scale: int,
    input_path: str,
    output_path: str,
    num_features: int,
    checkpoint_path: str | None = None,
    num_blocks: int = 4,
) -> None:
    """Run inference on one image or a directory of images."""

    input_files = collect_inputs(input_path)
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    normalized_name = model_name.lower()
    model = build_model(normalized_name, scale, num_features, num_blocks=num_blocks)
    ms = None
    if model is not None:
        ms = load_mindspore()
        ms.set_context(mode=ms.PYNATIVE_MODE, device_target="CPU")
        if load_checkpoint_if_available(model, checkpoint_path):
            print(f"Loaded checkpoint: {checkpoint_path}")
        model.set_train(False)

    for image_path in input_files:
        image = np.array(Image.open(image_path).convert("RGB"), dtype=np.uint8)
        if normalized_name == "bicubic":
            prediction = bicubic_upscale(image, scale)
        else:
            input_tensor = ms.Tensor(np.expand_dims(image_to_tensor(image), axis=0))
            output_tensor = model(input_tensor).asnumpy()
            prediction = tensor_to_image(output_tensor)

        target_path = output_dir / image_path.name
        save_image(prediction, target_path)
        print(f"Saved {model_name} result: {target_path}")
        print(f"Input size: {image.shape[1]}x{image.shape[0]} -> Output size: {prediction.shape[1]}x{prediction.shape[0]}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="MindSpore super-resolution inference")
    parser.add_argument("--model", default="imdn", choices=["bicubic", "imdn", "ca_imdn", "idb_imdn", "srcnn"])
    parser.add_argument("--scale", default=2, type=int)
    parser.add_argument("--num-features", default=32, type=int)
    parser.add_argument("--num-blocks", default=4, type=int)
    parser.add_argument("--checkpoint", default="", type=str)
    parser.add_argument("--input", required=True, type=str)
    parser.add_argument("--output", required=True, type=str)
    return parser.parse_args()


def main() -> None:
    """Entrypoint for inference."""

    args = parse_args()
    run_inference(
        model_name=args.model,
        scale=args.scale,
        input_path=args.input,
        output_path=args.output,
        num_features=args.num_features,
        checkpoint_path=args.checkpoint or None,
        num_blocks=args.num_blocks,
    )


if __name__ == "__main__":
    main()
