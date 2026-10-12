"""决策融合：把多个小模型 Signal 融合为统一态势评估（风险分 + 等级 + 归因）。

融合策略（可解释、可调）：
- 加权融合各信号 risk，权重来自 config；缺失信号按权重重归一化，不静默当 0。
- 用各信号 confidence 做置信加权，低置信信号对总风险影响打折。
- 记录每个信号的贡献，供决策层解释与飞轮"协同分歧"挖掘。
"""
from __future__ import annotations

from dataclasses import dataclass, field


# 信号名 → 配置权重键（dialog_rag 在设计语境里即"知识"信号）
_WEIGHT_KEY = {"forecast": "forecast", "detection": "detection", "dialog_rag": "knowledge"}


@dataclass
class SituationAssessment:
    risk_score: float                 # [0,1]
    risk_level: str                   # low / medium / high
    contributions: list[dict] = field(default_factory=list)
    fused_confidence: float = 0.0
    signals: dict = field(default_factory=dict)   # name -> Signal


def fuse(signals: list, cfg) -> SituationAssessment:
    weights = cfg.get("fusion", "weights", default={})
    avail = [s for s in signals if s.available]

    if not avail:
        return SituationAssessment(risk_score=0.0, risk_level="unknown",
                                   contributions=[], fused_confidence=0.0)

    def _w(name: str) -> float:
        return weights.get(_WEIGHT_KEY.get(name, name), 0.0)

    # 按可用信号重归一化权重
    wsum = sum(_w(s.name) for s in avail) or 1.0
    score = 0.0
    contributions = []
    for s in avail:
        w = _w(s.name) / wsum
        # 置信加权：低置信信号贡献打折(下限 0.5，避免完全忽略)
        eff = w * (0.5 + 0.5 * s.confidence)
        contrib = eff * s.risk
        score += contrib
        contributions.append({"signal": s.name, "weight": round(w, 3),
                              "risk": s.risk, "confidence": s.confidence,
                              "contribution": round(contrib, 3)})
    score = max(0.0, min(1.0, score))

    hi = cfg.get("fusion", "risk_high", default=0.66)
    med = cfg.get("fusion", "risk_medium", default=0.33)
    level = "high" if score >= hi else "medium" if score >= med else "low"

    fused_conf = round(sum(s.confidence for s in avail) / len(avail), 3)
    contributions.sort(key=lambda c: c["contribution"], reverse=True)
    return SituationAssessment(
        risk_score=round(score, 3), risk_level=level,
        contributions=contributions, fused_confidence=fused_conf,
        signals={s.name: s for s in signals})
