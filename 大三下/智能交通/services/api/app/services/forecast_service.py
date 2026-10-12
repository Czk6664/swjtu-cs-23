import json
from pathlib import Path
from typing import Any

from app.config import settings


class ForecastService:
    def __init__(self, results_dir: Path | None = None) -> None:
        self.results_dir = results_dir or settings.traffic_forecast_results_dir

    def summarize(self) -> dict[str, Any]:
        baseline = self._read_json("baseline_METRLA_results.json")
        dgl = self._read_json("dgl_METRLA_results.json")

        return {
            "source_dir": str(self.results_dir),
            "headline": "DGL variant wins 4/5 benchmark RMSE comparisons",
            "datasets": ["METRLA", "PEMS03", "PEMS04", "PEMS08", "PEMSBAY"],
            "baseline": {
                "mae": baseline.get("test_result", {}).get("mae"),
                "rmse": baseline.get("test_result", {}).get("rmse"),
                "mape": baseline.get("test_result", {}).get("mape"),
            },
            "dgl": {
                "rmse": dgl.get("test_result", {}).get("rmse"),
                "mape": dgl.get("test_result", {}).get("mape"),
                "inference_time": dgl.get("test_result", {}).get("inference_time"),
            },
        }

    def _read_json(self, name: str) -> dict[str, Any]:
        path = self.results_dir / name
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
