# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Scope

The active codebase in this repository is `sr_course_design/`, a MindSpore-based super-resolution course project focused on a CPU-runnable minimal experiment loop for the report.

## Common commands

Run commands from `sr_course_design/`.

### Environment and dependencies
- `pip install mindspore==2.8.0 -i https://repo.mindspore.cn/pypi/simple --trusted-host repo.mindspore.cn --extra-index-url https://repo.huaweicloud.com/repository/pypi/simple`
- `pip install pillow numpy pyyaml pytest`

### Smoke checks
- `python src/smoke_test_ms.py` — build SRCNN and IMDN and run one forward pass.
- `pytest` — run all tests.
- `pytest tests/test_dataset.py` — run one test file.
- `pytest tests/test_models.py -q` — run model shape tests only.
- `pytest tests/test_infer_smoke.py -q` — verify bicubic inference writes outputs.
- `pytest -k metrics` — run tests matching a keyword.

### Training / inference / evaluation
- `python src/train.py` — train with the default config (`src/configs/imdn_x2.yaml`).
- `python src/train.py src/configs/srcnn_x2.yaml`
- `python src/train.py src/configs/imdn_x2_edge.yaml`
- `python src/infer.py --model bicubic --scale 2 --input ./data/LR --output ./results/bicubic_x2`
- `python src/infer.py --model imdn --scale 2 --num-features 32 --input ./data/LR --output ./results/imdn_x2`
- `python src/eval.py --results ./results/imdn_x2 --targets ./data/HR --scale 2 --csv ./results/imdn_x2_metrics.csv`

## Data layout

Training and evaluation expect paired images under:

```text
<data_root>/
├── LR/
│   ├── 0001.png
│   └── ...
└── HR/
    ├── 0001.png
    └── ...
```

Constraints enforced by the code:
- LR and HR filenames must match.
- HR dimensions must equal `LR * scale`.
- Training only creates samples from images at least as large as `patch_size` in the YAML config.

## Architecture overview

### Main pipeline
- `src/train.py` contains the end-to-end training loop.
  - `TrainConfig` is loaded directly from YAML.
  - `SuperResolutionTrainer` builds the model, wraps `CombinedLoss`, batches in-memory samples, runs manual gradient steps with MindSpore, and saves one checkpoint at the end.
- `src/infer.py` is the prediction entrypoint.
  - Supports three modes: `bicubic` baseline, `srcnn`, and `imdn`.
  - MindSpore is imported lazily so bicubic inference can run without loading the framework.
- `src/eval.py` evaluates generated images against HR references.
  - Computes PSNR and a lightweight global SSIM.
  - By default evaluates on the Y channel after cropping `scale` pixels from borders.

### Models and loss
- `src/models/srcnn.py` implements the baseline SRCNN: resize first, then three convolutions.
- `src/models/imdn.py` implements a lightweight IMDN-style network with:
  - head feature extraction
  - stacked `DistillationBlock`s with residual fusion
  - pixel-shuffle upsampling
  - final RGB reconstruction
- `src/losses/combined_loss.py` combines L1 reconstruction loss with optional edge-aware loss. YAML configs toggle this through `use_edge_loss`.

### Dataset utilities
- `src/datasets/sr_dataset.py` is the shared image/data layer used by both training and inference.
- It handles:
  - LR/HR filename pairing
  - image load/save
  - random aligned LR/HR patch extraction
  - HWC/CHW and uint8/float conversions
- Training currently loads image pairs into Python lists and batches them manually; there is no MindSpore dataset pipeline yet.

### Tests
- `tests/test_dataset.py` covers filename pairing, aligned patch extraction, and tensor/image conversion.
- `tests/test_models.py` checks output shapes for SRCNN and IMDN forward passes and skips automatically if MindSpore is unavailable.
- `tests/test_metrics.py` covers PSNR/SSIM helpers from `src/eval.py`.
- `tests/test_infer_smoke.py` is a file-output smoke test for bicubic inference.

## Configs

The YAML files in `src/configs/` are the experiment presets actually used by the scripts:
- `srcnn_x2.yaml` — SRCNN baseline.
- `imdn_x2.yaml` — default IMDN training preset.
- `imdn_x2_edge.yaml` — alternate IMDN preset with the same model width but smaller batch/epoch settings than `imdn_x2.yaml`.

Important fields:
- `model_name`
- `scale`
- `batch_size`
- `epochs`
- `patch_size`
- `num_features`
- `use_edge_loss`
- `dataset_dir`
- `checkpoint_dir`
- `result_dir`

## Notes for future edits

- `src/train.py` and learned-model inference in `src/infer.py` explicitly run MindSpore on CPU; `src/smoke_test_ms.py` only sets PYNATIVE mode.
- `src/infer.py` does not load checkpoints yet, so `srcnn` and `imdn` inference currently use freshly initialized weights unless that script is extended.
- `src/train.py` currently samples one random LR/HR patch per source image per run, then batches those in memory; there is no MindSpore dataset pipeline yet.
- `src/train.py` currently does not consume `eval_dir` or `result_dir` during training; those values only exist in the config schema.
- Imports are split between `src.<module>` style in application code and direct module imports in tests after adding `src/` to `sys.path`; keep that difference in mind when moving files.
