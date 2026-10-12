"""Training entrypoint for lightweight MindSpore super-resolution project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mindspore as ms
import mindspore.nn as nn
import numpy as np
import csv
import sys
import time
import yaml
from mindspore import Tensor, ops

from src.datasets.sr_dataset import (
    DatasetConfig,
    image_to_tensor,
    list_image_pairs,
    load_image_pair,
    random_patch,
    tensor_to_image,
)
from src.eval import calculate_psnr, calculate_ssim
from src.losses.combined_loss import CombinedLoss
from src.models.imdn import CAIMDN, IDBIMDN, IMDN
from src.models.srcnn import SRCNN


@dataclass(frozen=True)
class TrainConfig:
    """Configuration loaded from yaml file."""

    model_name: str
    scale: int
    batch_size: int
    epochs: int
    learning_rate: float
    patch_size: int
    num_features: int
    use_edge_loss: bool
    dataset_dir: str
    eval_dir: str
    checkpoint_dir: str
    result_dir: str
    log_csv_path: str
    patches_per_image: int = 1
    edge_weight: float = 0.05
    use_laplacian_loss: bool = False
    laplacian_weight: float = 0.01
    max_train_pairs: int | None = None
    max_val_pairs: int | None = None
    num_blocks: int = 4
    attention_reduction: int = 4
    scheduler: str = "none"
    lr_step_milestones: list[int] | None = None
    lr_step_gamma: float = 0.5
    min_learning_rate: float = 1e-6


class SuperResolutionTrainer:
    """Manage model, loss, optimizer, and training data creation."""

    def __init__(self, config: TrainConfig) -> None:
        self.config = config
        self.model = self.build_model()
        self.loss_fn = CombinedLoss(
            use_edge_loss=config.use_edge_loss,
            edge_weight=config.edge_weight,
            use_laplacian_loss=config.use_laplacian_loss,
            laplacian_weight=config.laplacian_weight,
        )
        self.optimizer: nn.Adam | None = None
        self.grad_fn = None

    def build_model(self):
        normalized_name = self.config.model_name.lower()
        if normalized_name.startswith("srcnn"):
            return SRCNN(scale=self.config.scale)
        if normalized_name.startswith("ca_imdn"):
            return CAIMDN(
                scale=self.config.scale,
                num_features=self.config.num_features,
                num_blocks=self.config.num_blocks,
                attention_reduction=self.config.attention_reduction,
            )
        if normalized_name.startswith("idb_imdn"):
            return IDBIMDN(
                scale=self.config.scale,
                num_features=self.config.num_features,
                num_blocks=self.config.num_blocks,
            )
        return IMDN(scale=self.config.scale, num_features=self.config.num_features, num_blocks=self.config.num_blocks)

    def build_learning_rate(self, steps_per_epoch: int) -> float | list[float]:
        total_steps = self.config.epochs * steps_per_epoch
        scheduler = self.config.scheduler.lower()
        base_lr = self.config.learning_rate
        if scheduler == "none":
            return base_lr
        if scheduler == "step":
            milestones = self.config.lr_step_milestones or [max(1, self.config.epochs // 2)]
            values: list[float] = []
            for epoch in range(1, self.config.epochs + 1):
                decay_count = sum(1 for milestone in milestones if epoch > milestone)
                lr = max(self.config.min_learning_rate, base_lr * (self.config.lr_step_gamma ** decay_count))
                values.extend([lr] * steps_per_epoch)
            return values[:total_steps]
        if scheduler == "cosine":
            values = []
            for step in range(total_steps):
                progress = step / max(1, total_steps - 1)
                cosine = 0.5 * (1.0 + np.cos(np.pi * progress))
                values.append(self.config.min_learning_rate + (base_lr - self.config.min_learning_rate) * cosine)
            return values
        raise ValueError(f"Unsupported scheduler: {self.config.scheduler}")

    def lr_for_epoch(self, epoch: int) -> float:
        scheduler = self.config.scheduler.lower()
        base_lr = self.config.learning_rate
        if scheduler == "none":
            return base_lr
        if scheduler == "step":
            milestones = self.config.lr_step_milestones or [max(1, self.config.epochs // 2)]
            decay_count = sum(1 for milestone in milestones if epoch > milestone)
            return max(self.config.min_learning_rate, base_lr * (self.config.lr_step_gamma ** decay_count))
        if scheduler == "cosine":
            progress = (epoch - 1) / max(1, self.config.epochs - 1)
            cosine = 0.5 * (1.0 + np.cos(np.pi * progress))
            return float(self.config.min_learning_rate + (base_lr - self.config.min_learning_rate) * cosine)
        raise ValueError(f"Unsupported scheduler: {self.config.scheduler}")

    def initialize_optimizer(self, steps_per_epoch: int) -> None:
        learning_rate = self.build_learning_rate(steps_per_epoch)
        self.optimizer = nn.Adam(self.model.trainable_params(), learning_rate=learning_rate)
        self.grad_fn = ms.value_and_grad(self.forward_fn, None, self.optimizer.parameters)

    def load_split(self, root_dir: str | Path, max_pairs: int | None = None) -> list[tuple[np.ndarray, np.ndarray]]:
        dataset_config = DatasetConfig(root_dir=Path(root_dir), scale=self.config.scale)
        image_pairs = list_image_pairs(dataset_config)
        if not image_pairs:
            return []
        if max_pairs is not None:
            image_pairs = image_pairs[:max_pairs]

        samples: list[tuple[np.ndarray, np.ndarray]] = []
        for pair in image_pairs:
            loaded = load_image_pair(pair)
            lr_height, lr_width = loaded.lr_image.shape[:2]
            if lr_height < self.config.patch_size or lr_width < self.config.patch_size:
                continue

            for _ in range(max(1, self.config.patches_per_image)):
                lr_patch, hr_patch = random_patch(
                    loaded.lr_image,
                    loaded.hr_image,
                    patch_size=self.config.patch_size,
                    scale=self.config.scale,
                )
                samples.append((image_to_tensor(lr_patch), image_to_tensor(hr_patch)))
        return samples

    def create_dataset(self) -> list[tuple[np.ndarray, np.ndarray]]:
        samples = self.load_split(self.config.dataset_dir, self.config.max_train_pairs)
        if not samples:
            raise ValueError(
                "No training samples were created. Ensure LR images are at least patch_size and aligned with HR by scale."
            )
        return samples

    def create_validation_dataset(self) -> list[tuple[np.ndarray, np.ndarray]]:
        samples = self.load_split(self.config.eval_dir, self.config.max_val_pairs)
        if not samples:
            print(f"Warning: no validation samples found in {self.config.eval_dir}; validation metrics will be skipped.")
        return samples

    def forward_fn(self, lr_batch: Tensor, hr_batch: Tensor) -> Tensor:
        prediction = self.model(lr_batch)
        return self.loss_fn(prediction, hr_batch)

    def train_step(self, lr_batch: Tensor, hr_batch: Tensor) -> float:
        if self.optimizer is None or self.grad_fn is None:
            raise RuntimeError("Optimizer is not initialized.")
        loss, grads = self.grad_fn(lr_batch, hr_batch)
        self.optimizer(grads)
        return float(loss.asnumpy())

    def batch_samples(self, samples: list[tuple[np.ndarray, np.ndarray]]) -> list[tuple[Tensor, Tensor]]:
        batched: list[tuple[Tensor, Tensor]] = []
        for index in range(0, len(samples), self.config.batch_size):
            batch = samples[index : index + self.config.batch_size]
            lr_batch = Tensor(np.stack([sample[0] for sample in batch], axis=0), ms.float32)
            hr_batch = Tensor(np.stack([sample[1] for sample in batch], axis=0), ms.float32)
            batched.append((lr_batch, hr_batch))
        return batched

    def evaluate_batch(self, lr_tensor: Tensor, hr_tensor: Tensor) -> tuple[float, float]:
        """Compute simple PSNR/SSIM on a single batch for monitoring."""

        prediction = self.model(lr_tensor).asnumpy()
        prediction_image = tensor_to_image(prediction)
        target_image = tensor_to_image(hr_tensor.asnumpy())
        return calculate_psnr(prediction_image, target_image), calculate_ssim(prediction_image, target_image)

    def evaluate_split(self, samples: list[tuple[np.ndarray, np.ndarray]]) -> tuple[float, float]:
        if not samples:
            return float("nan"), float("nan")
        batches = self.batch_samples(samples)
        psnrs: list[float] = []
        ssims: list[float] = []
        self.model.set_train(False)
        for lr_batch, hr_batch in batches:
            psnr_value, ssim_value = self.evaluate_batch(lr_batch, hr_batch)
            psnrs.append(psnr_value)
            ssims.append(ssim_value)
        self.model.set_train(True)
        return sum(psnrs) / len(psnrs), sum(ssims) / len(ssims)

    def checkpoint_path(self, suffix: str = "") -> Path:
        checkpoint_dir = Path(self.config.checkpoint_dir)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        suffix_text = f"_{suffix}" if suffix else ""
        return checkpoint_dir / f"{self.config.model_name}_x{self.config.scale}{suffix_text}.ckpt"

    def save_checkpoint(self, suffix: str = "") -> Path:
        checkpoint_path = self.checkpoint_path(suffix)
        ms.save_checkpoint(self.model, str(checkpoint_path))
        return checkpoint_path

    def train(self) -> None:
        train_samples = self.create_dataset()
        val_samples = self.create_validation_dataset()
        train_batches = self.batch_samples(train_samples)
        self.initialize_optimizer(steps_per_epoch=len(train_batches))
        self.model.set_train(True)
        training_start = time.perf_counter()
        best_val_psnr = float("-inf")
        best_checkpoint_path: Path | None = None

        print(f"Model: {self.config.model_name}")
        print(f"Epochs: {self.config.epochs}")
        print(f"Batch size: {self.config.batch_size}")
        print(f"Patches per image: {self.config.patches_per_image}")
        print(f"Edge loss: {self.config.use_edge_loss} (weight={self.config.edge_weight})")
        print(f"Laplacian loss: {self.config.use_laplacian_loss} (weight={self.config.laplacian_weight})")
        print(f"Scheduler: {self.config.scheduler}")
        print(f"Dataset directory: {self.config.dataset_dir}")
        print(f"Number of training samples: {len(train_samples)}")
        print(f"Number of validation samples: {len(val_samples)}")

        log_path = Path(self.config.log_csv_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", newline="", encoding="utf-8") as log_file:
            writer = csv.DictWriter(
                log_file,
                fieldnames=[
                    "epoch",
                    "train_loss",
                    "train_psnr",
                    "train_ssim",
                    "val_psnr",
                    "val_ssim",
                    "learning_rate",
                    "epoch_time_sec",
                ],
            )
            if log_file.tell() == 0:
                writer.writeheader()

            for epoch in range(1, self.config.epochs + 1):
                epoch_start = time.perf_counter()
                epoch_losses: list[float] = []
                epoch_psnrs: list[float] = []
                epoch_ssims: list[float] = []
                for lr_batch, hr_batch in train_batches:
                    loss_value = self.train_step(lr_batch, hr_batch)
                    epoch_losses.append(loss_value)
                    psnr_value, ssim_value = self.evaluate_batch(lr_batch, hr_batch)
                    epoch_psnrs.append(psnr_value)
                    epoch_ssims.append(ssim_value)
                mean_loss = sum(epoch_losses) / len(epoch_losses)
                mean_psnr = sum(epoch_psnrs) / len(epoch_psnrs)
                mean_ssim = sum(epoch_ssims) / len(epoch_ssims)
                val_psnr, val_ssim = self.evaluate_split(val_samples)
                if val_samples and np.isfinite(val_psnr) and val_psnr > best_val_psnr:
                    best_val_psnr = val_psnr
                    best_checkpoint_path = self.save_checkpoint("best_psnr")
                    print(f"Saved best PSNR checkpoint: {best_checkpoint_path} (val_PSNR={best_val_psnr:.4f})")
                epoch_time = time.perf_counter() - epoch_start
                current_lr = self.lr_for_epoch(epoch)
                print(
                    f"Epoch {epoch}/{self.config.epochs} - loss: {mean_loss:.6f} - PSNR: {mean_psnr:.4f} - SSIM: {mean_ssim:.4f}"
                    + (f" - val_PSNR: {val_psnr:.4f} - val_SSIM: {val_ssim:.4f}" if val_samples else "")
                    + f" - lr: {current_lr:.8f} - epoch_time: {epoch_time:.2f}s"
                )
                writer.writerow({
                    "epoch": epoch,
                    "train_loss": mean_loss,
                    "train_psnr": mean_psnr,
                    "train_ssim": mean_ssim,
                    "val_psnr": val_psnr,
                    "val_ssim": val_ssim,
                    "learning_rate": current_lr,
                    "epoch_time_sec": epoch_time,
                })
                log_file.flush()

        checkpoint_path = self.save_checkpoint()
        total_time = time.perf_counter() - training_start
        print(f"Saved checkpoint: {checkpoint_path}")
        if best_checkpoint_path is not None:
            print(f"Best PSNR checkpoint: {best_checkpoint_path} (val_PSNR={best_val_psnr:.4f})")
        print(f"Saved training log: {log_path}")
        print(f"Total training time: {total_time:.2f}s")


def load_config(config_path: str | Path) -> TrainConfig:
    """Load yaml configuration from disk."""

    with open(config_path, "r", encoding="utf-8") as file:
        raw: dict[str, Any] = yaml.safe_load(file)
    return TrainConfig(**raw)


def main(config_path: str | None = None) -> None:
    """Entrypoint for local training script."""

    ms.set_context(mode=ms.PYNATIVE_MODE, device_target="CPU")
    resolved_config = Path(config_path) if config_path else Path(__file__).resolve().parent / "configs" / "imdn_x2.yaml"
    config = load_config(resolved_config)
    trainer = SuperResolutionTrainer(config)
    trainer.train()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
