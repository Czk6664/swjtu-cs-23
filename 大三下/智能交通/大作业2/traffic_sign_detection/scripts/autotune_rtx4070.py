from __future__ import annotations

import argparse
import copy
import csv
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tt100k.classes import get_class_names, get_source_to_target


@dataclass
class Candidate:
    label: str
    imgsz: int
    batch: int
    workers: int
    model: str = "yolo11n.pt"
    amp: bool = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autotune a stable TT100K YOLO setup for an RTX 4070 Laptop GPU."
    )
    parser.add_argument(
        "--dataset-root",
        required=True,
        help="Path to YOLO-format TT100K dataset root (contains images/ and labels/).",
    )
    parser.add_argument(
        "--base-config",
        default="configs/experiments/yolo11n_tt100k_rtx4070.yaml",
        help="Base experiment yaml used as a starting point.",
    )
    parser.add_argument("--device", default="0", help='CUDA device id, for example "0".')
    parser.add_argument(
        "--output-dir",
        default="outputs/autotune_rtx4070",
        help="Directory for probe configs, reports, and generated final config.",
    )
    parser.add_argument(
        "--probe-epochs",
        type=int,
        default=1,
        help="Epochs per probe run. Keep this low on unstable laptops.",
    )
    parser.add_argument(
        "--probe-fraction",
        type=float,
        default=0.05,
        help="Training data fraction per probe run.",
    )
    parser.add_argument(
        "--risk-profile",
        choices=("stable", "balanced", "push"),
        default="stable",
        help="How aggressively to search. 'stable' leaves extra headroom.",
    )
    parser.add_argument(
        "--cooldown-seconds",
        type=int,
        default=20,
        help="Cooldown between probe runs to reduce thermal spikes.",
    )
    parser.add_argument(
        "--final-epochs",
        type=int,
        default=None,
        help="Override final training epochs in the generated best config.",
    )
    parser.add_argument(
        "--skip-worker-sweep",
        action="store_true",
        help="Skip the second-stage worker sweep.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def save_yaml(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def safe_decode_output(raw: bytes) -> str:
    for encoding in ("utf-8", "gb18030", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def to_project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def detect_gpu_info(device: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {"device": device, "torch_cuda_available": False}

    try:
        import torch

        info["torch_cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            index = int(device.split(",")[0])
            props = torch.cuda.get_device_properties(index)
            info["gpu_name"] = props.name
            info["total_vram_gb"] = round(props.total_memory / (1024**3), 2)
            free_mem, total_mem = torch.cuda.mem_get_info(index)
            info["free_vram_gb"] = round(free_mem / (1024**3), 2)
            info["reported_total_vram_gb"] = round(total_mem / (1024**3), 2)
    except Exception as exc:
        info["torch_error"] = str(exc)

    try:
        command = [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.free,driver_version,temperature.gpu,power.draw",
            "--format=csv,noheader,nounits",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=True)
        first_line = completed.stdout.strip().splitlines()[0]
        parts = [part.strip() for part in first_line.split(",")]
        if len(parts) >= 6:
            info["nvidia_smi"] = {
                "name": parts[0],
                "memory_total_mb": float(parts[1]),
                "memory_free_mb": float(parts[2]),
                "driver_version": parts[3],
                "temperature_c": float(parts[4]),
                "power_draw_w": float(parts[5]),
            }
    except Exception as exc:
        info["nvidia_smi_error"] = str(exc)

    return info


def build_dataset_yaml(dataset_root: Path, output_path: Path) -> Path:
    data = {
        "path": to_project_relative(dataset_root),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": get_class_names(),
        "source_to_target": get_source_to_target(),
    }
    save_yaml(data, output_path)
    return output_path


def pick_stage_one_candidates(total_vram_gb: float, risk_profile: str) -> List[Candidate]:
    if total_vram_gb >= 8.0:
        base = [
            Candidate("probe_i512_b4_w2", imgsz=512, batch=4, workers=2),
            Candidate("probe_i512_b8_w2", imgsz=512, batch=8, workers=2),
            Candidate("probe_i640_b8_w2", imgsz=640, batch=8, workers=2),
            Candidate("probe_i640_b12_w2", imgsz=640, batch=12, workers=2),
            Candidate("probe_i640_b16_w2", imgsz=640, batch=16, workers=2),
            Candidate("probe_i704_b8_w2", imgsz=704, batch=8, workers=2),
        ]
    else:
        base = [
            Candidate("probe_i512_b4_w2", imgsz=512, batch=4, workers=2),
            Candidate("probe_i512_b8_w2", imgsz=512, batch=8, workers=2),
            Candidate("probe_i640_b6_w2", imgsz=640, batch=6, workers=2),
            Candidate("probe_i640_b8_w2", imgsz=640, batch=8, workers=2),
            Candidate("probe_i640_b12_w2", imgsz=640, batch=12, workers=2),
        ]

    if risk_profile == "stable":
        return base
    if risk_profile == "balanced":
        return base + [Candidate("probe_i704_b10_w2", imgsz=704, batch=10, workers=2)]
    return base + [
        Candidate("probe_i704_b10_w2", imgsz=704, batch=10, workers=2),
        Candidate("probe_i768_b8_w2", imgsz=768, batch=8, workers=2),
    ]


def build_worker_sweep(best: Candidate) -> List[Candidate]:
    return [
        Candidate(
            f"probe_i{best.imgsz}_b{best.batch}_w0",
            imgsz=best.imgsz,
            batch=best.batch,
            workers=0,
            model=best.model,
            amp=best.amp,
        ),
        Candidate(
            f"probe_i{best.imgsz}_b{best.batch}_w2",
            imgsz=best.imgsz,
            batch=best.batch,
            workers=2,
            model=best.model,
            amp=best.amp,
        ),
        Candidate(
            f"probe_i{best.imgsz}_b{best.batch}_w4",
            imgsz=best.imgsz,
            batch=best.batch,
            workers=4,
            model=best.model,
            amp=best.amp,
        ),
    ]


def build_probe_config(
    base_config: Dict[str, Any],
    dataset_yaml: Path,
    output_dir: Path,
    candidate: Candidate,
    device: str,
    probe_epochs: int,
    probe_fraction: float,
) -> Path:
    config = copy.deepcopy(base_config)
    config["model"] = candidate.model

    train_args = dict(config.get("train", {}))
    train_args.update(
        {
            "data": str(dataset_yaml.resolve()),
            "epochs": probe_epochs,
            "imgsz": candidate.imgsz,
            "batch": candidate.batch,
            "workers": candidate.workers,
            "device": device,
            "amp": candidate.amp,
            "cache": False,
            "project": to_project_relative(output_dir / "probe_runs"),
            "name": candidate.label,
            "fraction": probe_fraction,
            "patience": 0,
            "save": True,
            "plots": False,
            "exist_ok": True,
        }
    )
    config["train"] = train_args

    val_args = dict(config.get("val", {}))
    val_args.update(
        {
            "data": to_project_relative(dataset_yaml),
            "imgsz": candidate.imgsz,
            "batch": candidate.batch,
            "device": device,
            "workers": min(candidate.workers, 2),
        }
    )
    config["val"] = val_args

    predict_args = dict(config.get("predict", {}))
    predict_args.update({"imgsz": candidate.imgsz})
    config["predict"] = predict_args

    config_path = output_dir / "probe_configs" / f"{candidate.label}.yaml"
    save_yaml(config, config_path)
    return config_path


def read_last_metrics(results_csv: Path) -> Dict[str, float]:
    if not results_csv.exists():
        return {}
    with results_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {}
    latest = rows[-1]
    parsed: Dict[str, float] = {}
    for key, value in latest.items():
        if value in ("", None):
            continue
        try:
            parsed[key] = float(value)
        except ValueError:
            continue
    return parsed


def run_probe(candidate: Candidate, config_path: Path, output_dir: Path) -> Dict[str, Any]:
    command = [sys.executable, "train.py", "--config", str(config_path)]
    started_at = time.time()
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
    )
    duration_seconds = round(time.time() - started_at, 2)

    run_dir = output_dir / "probe_runs" / candidate.label
    metrics = read_last_metrics(run_dir / "results.csv")
    stdout_text = safe_decode_output(completed.stdout or b"")
    stderr_text = safe_decode_output(completed.stderr or b"")

    return {
        "candidate": asdict(candidate),
        "success": completed.returncode == 0,
        "returncode": completed.returncode,
        "duration_seconds": duration_seconds,
        "run_dir": to_project_relative(run_dir),
        "results_csv": to_project_relative(run_dir / "results.csv"),
        "metrics": metrics,
        "stdout_tail": stdout_text[-4000:],
        "stderr_tail": stderr_text[-4000:],
    }


def score_probe(result: Dict[str, Any]) -> float:
    metrics = result.get("metrics", {})
    epoch_time = metrics.get("time", result.get("duration_seconds", 1.0))
    epoch_time = max(epoch_time, 1.0)
    candidate = result["candidate"]
    quality_term = candidate["imgsz"] / 128.0
    batch_term = min(candidate["batch"], 16) / 4.0
    speed_term = 120.0 / epoch_time
    worker_penalty = candidate["workers"] * 0.15
    return round(quality_term + batch_term + speed_term - worker_penalty, 4)


def choose_best(results: List[Dict[str, Any]], risk_profile: str) -> Optional[Dict[str, Any]]:
    stable = [result for result in results if result.get("success")]
    if not stable:
        return None

    for result in stable:
        result["score"] = score_probe(result)

    highest_imgsz = max(result["candidate"]["imgsz"] for result in stable)
    top = [result for result in stable if result["candidate"]["imgsz"] == highest_imgsz]
    top.sort(key=lambda item: (item["candidate"]["batch"], -item["candidate"]["workers"], item["score"]))

    if risk_profile == "stable" and len(top) >= 2:
        preferred_batch = top[-2]["candidate"]["batch"]
        safer = [item for item in top if item["candidate"]["batch"] == preferred_batch]
        safer.sort(key=lambda item: (item["candidate"]["workers"], -item["score"]))
        return safer[0]

    top.sort(
        key=lambda item: (
            item["candidate"]["imgsz"],
            item["candidate"]["batch"],
            -item["score"],
            -item["candidate"]["workers"],
        )
    )
    return top[-1]


def write_final_config(
    base_config: Dict[str, Any],
    dataset_yaml: Path,
    output_dir: Path,
    best_result: Dict[str, Any],
    device: str,
    final_epochs: Optional[int],
) -> Path:
    config = copy.deepcopy(base_config)
    candidate = best_result["candidate"]

    train_args = dict(config.get("train", {}))
    train_args.update(
        {
            "data": to_project_relative(dataset_yaml),
            "imgsz": candidate["imgsz"],
            "batch": candidate["batch"],
            "workers": candidate["workers"],
            "device": device,
            "amp": candidate["amp"],
            "cache": False,
            "project": "outputs/runs",
            "name": "yolo11n_tt100k_rtx4070_autotuned",
        }
    )
    if final_epochs is not None:
        train_args["epochs"] = final_epochs
    config["train"] = train_args

    val_args = dict(config.get("val", {}))
    val_args.update(
        {
            "data": to_project_relative(dataset_yaml),
            "imgsz": candidate["imgsz"],
            "batch": candidate["batch"],
            "device": device,
            "workers": min(candidate["workers"], 2),
        }
    )
    config["val"] = val_args

    predict_args = dict(config.get("predict", {}))
    predict_args.update({"imgsz": candidate["imgsz"]})
    config["predict"] = predict_args
    config["model"] = candidate["model"]

    final_config = output_dir / "generated" / "best_rtx4070.yaml"
    save_yaml(config, final_config)
    return final_config


def save_report(report: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    base_config_path = (PROJECT_ROOT / args.base_config).resolve()
    dataset_root = Path(args.dataset_root).resolve()
    output_dir = (PROJECT_ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not (dataset_root / "images").exists():
        raise FileNotFoundError(f"dataset root does not contain images/: {dataset_root}")
    if not (dataset_root / "labels").exists():
        raise FileNotFoundError(f"dataset root does not contain labels/: {dataset_root}")

    base_config = load_yaml(base_config_path)
    gpu_info = detect_gpu_info(args.device)
    total_vram_gb = float(gpu_info.get("total_vram_gb") or 8.0)
    dataset_yaml = build_dataset_yaml(dataset_root, output_dir / "generated" / "tt100k_runtime.yaml")

    stage_one_candidates = pick_stage_one_candidates(total_vram_gb, args.risk_profile)
    probe_results: List[Dict[str, Any]] = []

    print("== GPU info ==")
    print(json.dumps(gpu_info, ensure_ascii=False, indent=2))
    print("== Stage 1: memory/quality sweep ==")

    for candidate in stage_one_candidates:
        config_path = build_probe_config(
            base_config=base_config,
            dataset_yaml=dataset_yaml,
            output_dir=output_dir,
            candidate=candidate,
            device=args.device,
            probe_epochs=args.probe_epochs,
            probe_fraction=args.probe_fraction,
        )
        print(f"[probe] {candidate.label} imgsz={candidate.imgsz} batch={candidate.batch} workers={candidate.workers}")
        result = run_probe(candidate, config_path, output_dir)
        probe_results.append(result)
        print(f"  success={result['success']} returncode={result['returncode']} duration={result['duration_seconds']}s")
        if args.cooldown_seconds > 0:
            time.sleep(args.cooldown_seconds)

    best_result = choose_best(probe_results, args.risk_profile)
    if best_result is None:
        report = {
        "gpu_info": gpu_info,
        "dataset_root": to_project_relative(dataset_root),
        "base_config": to_project_relative(base_config_path),
        "risk_profile": args.risk_profile,
        "probe_results": probe_results,
        "best_result": None,
        "message": "No stable probe succeeded. Use a lower imgsz, smaller batch, or stronger cooling.",
        }
        save_report(report, output_dir / "autotune_report.json")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    if not args.skip_worker_sweep:
        print("== Stage 2: worker sweep ==")
        worker_candidates = build_worker_sweep(Candidate(**best_result["candidate"]))
        worker_results: List[Dict[str, Any]] = []
        seen_labels = {result["candidate"]["label"] for result in probe_results}
        for candidate in worker_candidates:
            if candidate.label in seen_labels:
                continue
            config_path = build_probe_config(
                base_config=base_config,
                dataset_yaml=dataset_yaml,
                output_dir=output_dir,
                candidate=candidate,
                device=args.device,
                probe_epochs=args.probe_epochs,
                probe_fraction=args.probe_fraction,
            )
            print(f"[probe] {candidate.label} imgsz={candidate.imgsz} batch={candidate.batch} workers={candidate.workers}")
            result = run_probe(candidate, config_path, output_dir)
            worker_results.append(result)
            print(f"  success={result['success']} returncode={result['returncode']} duration={result['duration_seconds']}s")
            if args.cooldown_seconds > 0:
                time.sleep(args.cooldown_seconds)

        probe_results.extend(worker_results)
        best_result = choose_best(probe_results, args.risk_profile)
        if best_result is None:
            raise RuntimeError("A best result was expected after worker sweep, but none was found.")

    final_config = write_final_config(
        base_config=base_config,
        dataset_yaml=dataset_yaml,
        output_dir=output_dir,
        best_result=best_result,
        device=args.device,
        final_epochs=args.final_epochs,
    )

    report = {
        "gpu_info": gpu_info,
        "dataset_root": to_project_relative(dataset_root),
        "base_config": to_project_relative(base_config_path),
        "risk_profile": args.risk_profile,
        "probe_results": probe_results,
        "best_result": best_result,
        "final_config": to_project_relative(final_config),
    }
    save_report(report, output_dir / "autotune_report.json")

    print("== Best result ==")
    print(json.dumps(best_result, ensure_ascii=False, indent=2))
    print(f"Generated final config: {final_config}")


if __name__ == "__main__":
    main()
