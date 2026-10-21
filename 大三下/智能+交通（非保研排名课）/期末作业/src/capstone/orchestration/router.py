"""路由：根据场景/请求决定调用哪些小模型，控制成本（大模型按需）。

workflow 显式指定时按指定；否则按场景内容推断。返回要调用的适配器名集合。
"""
from __future__ import annotations

ALL = {"forecast", "detection", "dialog_rag"}

_WORKFLOW_MAP = {
    "full-decision": ALL,
    "congestion": {"forecast", "dialog_rag"},
    "intersection-risk": {"forecast", "detection", "dialog_rag"},
    "sign-only": {"detection"},
    "prediction-only": {"forecast"},
}


def route(scene: dict) -> set[str]:
    wf = scene.get("workflow")
    if wf in _WORKFLOW_MAP:
        return set(_WORKFLOW_MAP[wf])
    selected = set()
    if "traffic_load" in scene or "forecast_dataset" in scene:
        selected.add("forecast")
    if scene.get("detections"):
        selected.add("detection")
    selected.add("dialog_rag")  # 知识源默认参与，便于解释/溯源
    return selected or ALL
