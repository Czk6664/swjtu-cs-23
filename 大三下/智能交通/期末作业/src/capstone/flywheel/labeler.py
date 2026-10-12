"""策展标注：把难例整理成版本化数据集快照（含 manifest，可复现）。

offline 模式下用启发式/大模型占位自动标注；真实部署可接人工复核界面。
快照只存样本引用 + manifest（不搬大文件），manifest 记录来源/数量/方式/哈希/时间。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def label_snapshot(hard_cases: list[dict], snapshots_dir: Path, model_name: str,
                   version: str) -> dict:
    snap_dir = Path(snapshots_dir) / f"{model_name}_{version}"
    snap_dir.mkdir(parents=True, exist_ok=True)

    labeled = []
    for hc in hard_cases:
        labeled.append({
            "inference_id": hc.get("inference_id"),
            "input_ref": hc.get("input_ref"),
            "mined_reason": hc.get("mined_reason"),
            # 自动标注占位：真实场景由 LLM/人工给出修正标签
            "auto_label": _auto_label(hc),
        })
    (snap_dir / "samples.json").write_text(
        json.dumps(labeled, ensure_ascii=False, indent=2), encoding="utf-8")

    digest = hashlib.md5(
        json.dumps(labeled, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    manifest = {
        "model": model_name, "version": version,
        "num_samples": len(labeled),
        "labeling": "auto(offline-stub)",
        "reasons": _reason_counts(labeled),
        "hash": digest,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (snap_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _auto_label(hc: dict) -> str:
    reason = hc.get("mined_reason", "")
    if "disagreement" in reason:
        return "需人工裁决：大小模型结论冲突"
    if "low_confidence" in reason:
        return "建议补充同类样本以提升置信"
    if "retrieval" in reason:
        return "建议补充/更新知识库条目"
    return "待复核"


def _reason_counts(labeled: list[dict]) -> dict:
    out: dict[str, int] = {}
    for x in labeled:
        r = (x.get("mined_reason") or "other").split("(")[0]
        out[r] = out.get(r, 0) + 1
    return out
