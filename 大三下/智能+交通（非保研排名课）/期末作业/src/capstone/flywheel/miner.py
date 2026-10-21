"""难例挖掘：从遥测中按规则选出值得重训/补知识库的样本。

规则（阈值来自 config）：
- 低置信：confidence < 阈值。
- 协同分歧：flagged_reason 含 disagreement（决策层已标）。
- 已标记：任何 flagged_reason 非空（如检索未命中、误差超阈）。
"""
from __future__ import annotations

import json


def mine_hard_cases(telemetry: list[dict], cfg, model_name: str | None = None) -> list[dict]:
    conf_thr = cfg.get("flywheel", "mining", "det_conf_threshold", default=0.35)
    hard = []
    for row in telemetry:
        if model_name and row.get("model_name") != model_name:
            continue
        reason = None
        if (row.get("confidence") or 0.0) < conf_thr:
            reason = f"low_confidence(<{conf_thr})"
        elif row.get("flagged_reason"):
            reason = row["flagged_reason"]
        else:
            verdict = _loads(row.get("big_model_verdict"))
            if verdict.get("disagreements"):
                reason = "model_disagreement"
        if reason:
            hard.append({**row, "mined_reason": reason})
    return hard


def _loads(s):
    if isinstance(s, dict):
        return s
    try:
        return json.loads(s) if s else {}
    except (TypeError, ValueError):
        return {}
