"""决策与解释：把态势评估转成 建议动作 + 风险等级 + 可解释/可溯源理由。

替换根 services/api 的规则桩 DecisionService。理由由两部分组成：
1. 结构化归因（哪个信号贡献最大、置信如何）——确定性、可审计。
2. 自然语言解释——交给大作业3 的 LLM provider（offline 时为模板，接 DeepSeek 后为生成）。

同时计算"协同分歧"标记：当某小模型原始结论与融合判断相反时记录，供飞轮难例挖掘。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .fusion import SituationAssessment

# 风险等级 → 建议动作模板
_ACTION = {
    "high": "立即介入：加大该路段信号配时/警力，发布拥堵与管制预警，引导绕行。",
    "medium": "重点关注：提高监测频率，准备预案，必要时发布出行提示。",
    "low": "常规运行：维持监测，无需特别干预。",
    "unknown": "数据不足：建议人工核查，补充感知输入后再决策。",
}


@dataclass
class Decision:
    action: str
    risk_level: str
    risk_score: float
    confidence: float
    rationale: str                       # 结构化理由
    explanation: str = ""                # 自然语言解释(LLM)
    disagreements: list[dict] = field(default_factory=list)


def decide(assess: SituationAssessment, cfg, dialog_adapter=None) -> Decision:
    action = _ACTION.get(assess.risk_level, _ACTION["unknown"])

    # 结构化理由：列出主要贡献信号
    if assess.contributions:
        top = assess.contributions[0]
        parts = [f"综合风险 {assess.risk_score:.2f}（{assess.risk_level}）。",
                 f"主因 {top['signal']}（贡献 {top['contribution']}，风险 {top['risk']}，"
                 f"置信 {top['confidence']}）。"]
        for c in assess.contributions[1:]:
            parts.append(f"次因 {c['signal']}（贡献 {c['contribution']}）。")
        rationale = " ".join(parts)
    else:
        rationale = "无可用信号，建议人工核查。"

    disagreements = _detect_disagreements(assess)

    # 自然语言解释（可选，复用大作业3 LLM）
    explanation = ""
    if dialog_adapter is not None:
        evidence = f"决策依据:\n- 态势: {rationale}\n- 建议: {action}"
        try:
            explanation = dialog_adapter.explain("请解释本次交通决策的理由", evidence)
        except Exception:
            explanation = ""

    return Decision(
        action=action, risk_level=assess.risk_level, risk_score=assess.risk_score,
        confidence=assess.fused_confidence, rationale=rationale,
        explanation=explanation, disagreements=disagreements)


def _detect_disagreements(assess: SituationAssessment) -> list[dict]:
    """小模型原始风险与融合等级相反 → 记为协同分歧（飞轮高价值难例）。"""
    out = []
    for name, sig in assess.signals.items():
        if not getattr(sig, "available", False):
            continue
        # 小模型判低(<0.33) 但融合判 high，或反之
        if sig.risk < 0.33 and assess.risk_level == "high":
            out.append({"signal": name, "type": "small-low-vs-fused-high",
                        "signal_risk": sig.risk, "fused": assess.risk_score})
        elif sig.risk > 0.66 and assess.risk_level == "low":
            out.append({"signal": name, "type": "small-high-vs-fused-low",
                        "signal_risk": sig.risk, "fused": assess.risk_score})
    return out
