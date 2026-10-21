"""大作业1 交通流预测适配器（复用 travelqa.ForecastTool 读取 STAEformer 结果）。

把预测误差/规模映射为『拥堵风险 + 置信度』：
- MAPE 越高 → 预测越不准 → 置信度越低（也是飞轮难例信号）。
- 这里用预测的相对误差与场景给定的"当前流量水平"共同估计拥堵风险。
"""
from __future__ import annotations

from .base import Signal


class ForecastAdapter:
    name = "forecast"

    def __init__(self, cfg):
        from travelqa.config import Config as TqaConfig
        from travelqa.tools import ForecastTool
        tqa = TqaConfig.load()
        # 指向 workspace 内大作业1 结果目录
        tqa.data["integrations"]["forecast"]["results_dir"] = str(
            cfg.workspace_path(cfg.get("paths", "forecast_results")))
        self.tool = ForecastTool(tqa)

    def infer(self, scene: dict) -> Signal:
        dataset = scene.get("forecast_dataset", "PEMS08")
        variant = scene.get("forecast_variant", "baseline")
        s = self.tool.summarize(dataset=dataset, variant=variant)
        if not s.get("available"):
            return Signal(self.name, risk=0.0, confidence=0.0,
                          summary="预测结果不可用", raw=s, available=False)

        mape = float(s["overall"].get("mape") or 0.0)        # 百分比
        confidence = max(0.0, min(1.0, 1.0 - mape / 30.0))   # MAPE 30% 视为基本不可信
        # 拥堵风险：场景给的负载水平 [0,1] 主导，预测不确定性轻微抬高风险
        load = float(scene.get("traffic_load", 0.5))
        risk = max(0.0, min(1.0, 0.8 * load + 0.2 * (1 - confidence)))
        return Signal(
            self.name, risk=round(risk, 3), confidence=round(confidence, 3),
            summary=(f"{s['variant_cn']}@{dataset}: MAE {s['overall']['mae']}, "
                     f"MAPE {mape}% → 预测置信 {confidence:.2f}; 当前负载 {load} → 拥堵风险 {risk:.2f}"),
            raw=s)
