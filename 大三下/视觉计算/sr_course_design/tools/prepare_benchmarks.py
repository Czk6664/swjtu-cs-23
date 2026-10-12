"""Prepare Set5/Set14/BSD100/Urban100 benchmark folders.

The output layout is:

data/benchmarks/<name>/
  LR/
  HR/

The script first keeps any existing folders intact. If a benchmark is missing,
it tries the commonly used HuggingFace mirrors by eugenesiow and normalizes the
image filenames for this project's evaluation code.
"""

from __future__ import annotations

import argparse
import shutil
import tarfile
import urllib.request
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}

HF_REPOS = {
    "Set5": "eugenesiow/Set5",
    "Set14": "eugenesiow/Set14",
    "BSD100": "eugenesiow/BSD100",
    "Urban100": "eugenesiow/Urban100",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download or normalize SR benchmark datasets.")
    parser.add_argument("--root", default="./data/benchmarks", type=Path)
    parser.add_argument("--archive-root", default="./data/benchmark_archives", type=Path)
    parser.add_argument("--scale", default=2, type=int)
    parser.add_argument("--names", nargs="+", default=["Set5", "Set14", "BSD100", "Urban100"])
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def safe_extract(archive: tarfile.TarFile, target: Path) -> None:
    target = target.resolve()
    for member in archive.getmembers():
        member_path = (target / member.name).resolve()
        if not str(member_path).startswith(str(target)):
            raise RuntimeError(f"Unsafe archive member: {member.name}")
    archive.extractall(target)


def download_hf_file(repo_id: str, filename: str, archive_root: Path) -> Path:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency huggingface_hub. Install it with: "
            "pip install huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple"
        ) from exc

    archive_root.mkdir(parents=True, exist_ok=True)
    try:
        path = hf_hub_download(repo_id=repo_id, repo_type="dataset", filename=filename, cache_dir=str(archive_root))
        return Path(path)
    except Exception:
        endpoint = "https://hf-mirror.com"
        output_path = archive_root / repo_id.replace("/", "_") / filename.replace("/", "_")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"{endpoint}/datasets/{repo_id}/resolve/main/{filename}"
        print(f"[fallback] direct download: {url}")
        urllib.request.urlretrieve(url, output_path)
        return output_path


def image_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS)


def normalize_name(path: Path) -> str:
    stem = path.stem
    for token in ("_HR", "_hr", "_LR", "_lr", "_x2", "x2"):
        stem = stem.replace(token, "")
    return f"{stem}.png"


def copy_images(source_root: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for image_path in image_files(source_root):
        out_name = normalize_name(image_path)
        image = Image.open(image_path).convert("RGB")
        image.save(destination / out_name)


def align_hr_to_lr(hr_dir: Path, lr_dir: Path, scale: int) -> None:
    for lr_path in sorted(lr_dir.glob("*.png")):
        hr_path = hr_dir / lr_path.name
        if not hr_path.exists():
            continue
        lr_image = Image.open(lr_path).convert("RGB")
        hr_image = Image.open(hr_path).convert("RGB")
        expected = (lr_image.width * scale, lr_image.height * scale)
        if hr_image.size == expected:
            continue
        crop_width = min(hr_image.width, expected[0])
        crop_height = min(hr_image.height, expected[1])
        hr_image = hr_image.crop((0, 0, crop_width, crop_height))
        if hr_image.size != expected:
            hr_image = hr_image.resize(expected, Image.BICUBIC)
        hr_image.save(hr_path)


def prepare_from_hf(name: str, output_root: Path, archive_root: Path, scale: int) -> None:
    repo_id = HF_REPOS.get(name)
    if repo_id is None:
        raise ValueError(f"Unsupported benchmark: {name}")

    work_dir = archive_root / "extracted" / name
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    hr_archive = download_hf_file(repo_id, f"data/{name}_HR.tar.gz", archive_root)
    lr_archive = download_hf_file(repo_id, f"data/{name}_LR_x{scale}.tar.gz", archive_root)

    with tarfile.open(hr_archive, "r:gz") as tar:
        safe_extract(tar, work_dir / "HR_raw")
    with tarfile.open(lr_archive, "r:gz") as tar:
        safe_extract(tar, work_dir / "LR_raw")

    benchmark_dir = output_root / name
    if benchmark_dir.exists():
        shutil.rmtree(benchmark_dir)
    copy_images(work_dir / "HR_raw", benchmark_dir / "HR")
    copy_images(work_dir / "LR_raw", benchmark_dir / "LR")
    align_hr_to_lr(benchmark_dir / "HR", benchmark_dir / "LR", scale)


def main() -> None:
    args = parse_args()
    output_root = (PROJECT_ROOT / args.root).resolve() if not args.root.is_absolute() else args.root
    archive_root = (PROJECT_ROOT / args.archive_root).resolve() if not args.archive_root.is_absolute() else args.archive_root
    output_root.mkdir(parents=True, exist_ok=True)

    for name in args.names:
        benchmark_dir = output_root / name
        if args.skip_existing and (benchmark_dir / "LR").exists() and (benchmark_dir / "HR").exists():
            print(f"[skip] {name}: existing LR/HR folders found")
            continue
        try:
            prepare_from_hf(name, output_root, archive_root, args.scale)
            lr_count = len(list((benchmark_dir / "LR").glob("*.png")))
            hr_count = len(list((benchmark_dir / "HR").glob("*.png")))
            print(f"[ok] {name}: LR={lr_count}, HR={hr_count}, path={benchmark_dir}")
        except Exception as exc:
            print(f"[warn] {name}: {exc}")
            print("       You can also manually place images under data/benchmarks/<name>/LR and HR.")


if __name__ == "__main__":
    main()
