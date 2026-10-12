from pathlib import Path
from typing import Any

import yaml

from app.config import settings


class DetectionService:
    def __init__(self, dataset_config: Path | None = None, run_dir: Path | None = None) -> None:
        self.dataset_config = dataset_config or settings.traffic_detection_dataset_config
        self.run_dir = run_dir or settings.traffic_detection_run_dir

    def summarize(self) -> dict[str, Any]:
        dataset = self._read_yaml(self.dataset_config)
        metrics = self._read_latest_metrics()

        return {
            "dataset_config": str(self.dataset_config),
            "run_dir": str(self.run_dir),
            "classes": dataset.get("names", []),
            "num_classes": len(dataset.get("names", [])),
            "latest_metrics": metrics,
            "preview_assets": {
                "prediction_grid": "val_batch0_pred.jpg",
                "confusion_matrix_normalized": "confusion_matrix_normalized.png",
                "training_curve": "results.png",
            },
        }

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def _read_latest_metrics(self) -> dict[str, Any]:
        results_csv = self.run_dir / "results.csv"
        if not results_csv.exists():
            return {}

        last_line = results_csv.read_text(encoding="utf-8").strip().splitlines()[-1]
        metrics = last_line.split(",")
        return {
            "precision": metrics[5] if len(metrics) > 5 else None,
            "recall": metrics[6] if len(metrics) > 6 else None,
            "mAP50": metrics[7] if len(metrics) > 7 else None,
            "mAP50_95": metrics[8] if len(metrics) > 8 else None,
        }
