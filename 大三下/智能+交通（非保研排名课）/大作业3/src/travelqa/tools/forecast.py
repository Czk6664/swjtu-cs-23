"""高阶要求 —— 接入大作业1 (STAEformer 交通流预测)。

不重新训练/推理，而是读取大作业1 已产出的 results/*_results.json，把结构化指标
(整体 RMSE/MAE/MAPE、逐步误差、模型规模) 提供给大模型，支撑『交通流预测问答』。

文件命名规律(见大作业1/results): {variant}_{dataset}_results.json
  variant: baseline / dgl / la / mst ...   dataset: PEMS03/04/07/08 / METRLA / PEMSBAY
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_VARIANT_NAMES = {
    "baseline": "STAEformer 基线",
    "dgl": "动态图学习改进", "la": "轻量注意力改进", "mst": "多尺度时间改进",
}


class ForecastTool:
    def __init__(self, cfg):
        self.enabled = bool(cfg.get("integrations", "forecast", "enabled", default=False))
        self.results_dir = cfg.resolve_path(
            cfg.get("integrations", "forecast", "results_dir", default="../大作业1/results"))

    def available(self) -> bool:
        return self.enabled and Path(self.results_dir).exists()

    def list_runs(self) -> list[str]:
        if not Path(self.results_dir).exists():
            return []
        return sorted(p.stem.replace("_results", "")
                      for p in Path(self.results_dir).glob("*_results.json"))

    def summarize(self, dataset: str = "PEMS08", variant: str = "baseline") -> dict:
        """读取指定预测实验的结果摘要。文件缺失时返回 available=False，不抛异常。"""
        if not self.available():
            return {"available": False, "reason": "未启用或大作业1 results 目录不存在"}
        path = Path(self.results_dir) / f"{variant}_{dataset}_results.json"
        if not path.exists():
            return {"available": False, "reason": f"未找到 {path.name}",
                    "known_runs": self.list_runs()}
        with path.open(encoding="utf-8") as f:
            d = json.load(f)
        test = d.get("test_result", {})
        steps = test.get("step_results", [])
        return {
            "available": True,
            "dataset": dataset,
            "variant": variant,
            "variant_cn": _VARIANT_NAMES.get(variant, variant),
            "model_name": d.get("model_name"),
            "total_params": d.get("total_params"),
            "overall": {k: _f(test.get(k)) for k in ("rmse", "mae", "mape")},
            "horizon_steps": len(steps),
            "step_15min": _step(steps, 3),   # 5min/步, 第3步=15分钟
            "step_30min": _step(steps, 6),
            "step_60min": _step(steps, 12),
            "interpretation": (
                f"{_VARIANT_NAMES.get(variant, variant)}在 {dataset} 测试集整体 MAE "
                f"{_f(test.get('mae'))}、RMSE {_f(test.get('rmse'))}、MAPE {_f(test.get('mape'))}%。"
                "预测误差随时间步增大，短时(15分钟)预测最准。"
            ),
        }

    def predict(
        self,
        dataset: str = "PEMS08",
        variant: str = "baseline",
        node_id: int = 0,
        sample_index: int = -1,
    ) -> dict:
        """Run one real STAEformer inference window from homework 1.

        This uses the trained checkpoint plus the dataset test index to predict the
        next 12 time steps. It deliberately returns available=False instead of
        guessing when torch/model/data files are missing.
        """
        if not self.available():
            return {"available": False, "reason": "forecast integration is disabled or results_dir is missing"}

        try:
            import numpy as np
            import torch
            import yaml
        except Exception as exc:  # pragma: no cover - depends on deployment env
            return {"available": False, "reason": f"missing forecast runtime dependency: {exc}"}

        dataset = dataset.upper()
        root = Path(self.results_dir).parent
        data_dir = root / "data" / dataset
        checkpoint = Path(self.results_dir) / f"{variant}_{dataset}_checkpoint.pth"
        config_path = root / "STAEformer.yaml"
        model_path = root / "STAEformer.py"

        missing = [str(p) for p in (data_dir / "data.npz", data_dir / "index.npz", checkpoint, config_path, model_path) if not p.exists()]
        if missing:
            return {"available": False, "reason": "missing STAEformer prediction files", "missing": missing}

        try:
            with config_path.open(encoding="utf-8") as f:
                cfg = yaml.safe_load(f)[dataset]
            model_args = cfg["model_args"]
            num_nodes = int(model_args["num_nodes"])
            node_id = max(0, min(int(node_id), num_nodes - 1))

            data = np.load(data_dir / "data.npz")["data"].astype(np.float32)[..., [0, 1, 2]]
            index = np.load(data_dir / "index.npz")
            train_index = index["train"]
            test_index = index["test"]
            if len(test_index) == 0:
                return {"available": False, "reason": "test index is empty"}

            train_x_idx = _stack_ranges(train_index[:, 0], train_index[:, 1])
            mean = float(data[train_x_idx, :, 0].mean())
            std = float(data[train_x_idx, :, 0].std())
            if std == 0:
                return {"available": False, "reason": "training scaler std is zero"}

            sample = test_index[int(sample_index) % len(test_index)]
            x_idx = np.arange(sample[0], sample[1])
            y_idx = np.arange(sample[1], sample[2])
            x = data[x_idx][None, ...].copy()
            x[..., 0] = (x[..., 0] - mean) / std
            y_true = data[y_idx, node_id, 0].astype(float).tolist()

            module = _load_staeformer_module(model_path)
            model = module.STAEformer(**model_args)
            try:
                state = torch.load(checkpoint, map_location="cpu", weights_only=False)
            except TypeError:
                state = torch.load(checkpoint, map_location="cpu")
            if isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]
            if isinstance(state, dict) and "model_state_dict" in state:
                state = state["model_state_dict"]
            model.load_state_dict(state)
            model.eval()
            with torch.no_grad():
                out = model(torch.FloatTensor(x))
                out = out * std + mean
            pred = out.squeeze(0)[:, node_id, 0].cpu().numpy().astype(float).tolist()
            predictions = [
                {"step": i + 1, "minute": (i + 1) * 5, "flow": round(float(v), 3)}
                for i, v in enumerate(pred)
            ]
            trend = _trend(pred)
            return {
                "available": True,
                "mode": "real_inference",
                "dataset": dataset,
                "variant": variant,
                "model": "STAEformer",
                "checkpoint": str(checkpoint),
                "node_id": node_id,
                "sample_index": int(sample_index),
                "input_steps": len(x_idx),
                "horizon_steps": len(predictions),
                "step_minutes": 5,
                "horizon_minutes": len(predictions) * 5,
                "predictions": predictions,
                "trend": trend,
                "observed_last_flow": round(float(data[x_idx[-1], node_id, 0]), 3),
                "ground_truth_for_demo": [round(float(v), 3) for v in y_true],
                "note": "Uses a held-out test window from homework 1 for demonstrable STAEformer inference.",
            }
        except Exception as exc:
            return {"available": False, "reason": f"STAEformer prediction failed: {exc}"}


def _f(v):
    try:
        return round(float(v), 3)
    except (TypeError, ValueError):
        return v


def _step(steps: list, n: int):
    for s in steps:
        if s.get("step") == n:
            return {"step": n, "rmse": _f(s.get("rmse")), "mae": _f(s.get("mae")),
                    "mape": _f(s.get("mape"))}
    return None


def _stack_ranges(starts, stops):
    import numpy as np

    return np.concatenate([np.arange(int(s), int(e)) for s, e in zip(starts, stops)])


def _load_staeformer_module(path: Path):
    spec = importlib.util.spec_from_file_location("travelqa_homework1_staeformer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load STAEformer module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _trend(values: list[float]) -> str:
    if len(values) < 2:
        return "unknown"
    delta = float(values[-1]) - float(values[0])
    if delta > 5:
        return "rising"
    if delta < -5:
        return "falling"
    return "stable"
