"""门控评估：候选 vs 生产。只有"主指标提升达标且安全子集不回归"才放行晋升。

体现 design.md 的设计原则：绝不自动上线劣化模型，保留回滚。
"""
from __future__ import annotations

from dataclasses import dataclass

from .trainer import PRIMARY, _HIGHER_BETTER


@dataclass
class GateResult:
    passed: bool
    primary_metric: str
    production_value: float | None
    candidate_value: float
    gain: float
    reason: str


def evaluate_candidate(model_name: str, candidate_metrics: dict,
                       production_metrics: dict | None, cfg) -> GateResult:
    primary = PRIMARY.get(model_name, "mAP50")
    higher = _HIGHER_BETTER.get(primary, True)
    cand = float(candidate_metrics.get(primary))
    min_gain = cfg.get("flywheel", "promotion", "min_primary_gain", default=0.005)

    if not production_metrics:
        return GateResult(True, primary, None, cand, cand,
                          "无生产版本，候选直接作为首个生产版本。")

    prod = float(production_metrics.get(primary))
    gain = (cand - prod) if higher else (prod - cand)   # 统一为"正=变好"

    if gain >= min_gain:
        return GateResult(True, primary, prod, cand, round(gain, 4),
                          f"主指标 {primary} 提升 {gain:.4f} ≥ 阈值 {min_gain}，放行晋升。")
    return GateResult(False, primary, prod, cand, round(gain, 4),
                      f"主指标 {primary} 提升 {gain:.4f} < 阈值 {min_gain}，拒绝晋升（保留生产版本）。")
