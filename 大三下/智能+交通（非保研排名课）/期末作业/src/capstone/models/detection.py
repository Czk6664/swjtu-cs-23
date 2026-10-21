"""大作业2 交通标志检测适配器（复用 travelqa.DetectionTool 读取 YOLO/TT100K 结果）。

场景里给出本次检测到的标志（类别 + 置信度），适配器：
- 用模型整体 mAP50 作为该小模型的可靠性先验；
- 用检测到的"限制/禁令类"标志抬高风险；
- 单框低置信 → 作为飞轮难例信号。
"""
from __future__ import annotations

from .base import Signal

# 高风险语义前缀：禁令(p/pn)、限速(pl)、解除(pne) 一般意味着此处有管控/风险点
_RISK_PREFIXES = ("pl", "pn", "pne", "p", "w")


class DetectionAdapter:
    name = "detection"

    def __init__(self, cfg):
        from travelqa.config import Config as TqaConfig
        from travelqa.tools import DetectionTool
        tqa = TqaConfig.load()
        tqa.data["integrations"]["detection"]["dataset_yaml"] = str(
            cfg.workspace_path(cfg.get("paths", "detection_yaml")))
        tqa.data["integrations"]["detection"]["run_csv"] = str(
            cfg.workspace_path(cfg.get("paths", "detection_csv")))
        self.tool = DetectionTool(tqa)
        self._summary = self.tool.summarize()

    def infer(self, scene: dict) -> Signal:
        if not self._summary.get("available"):
            return Signal(self.name, risk=0.0, confidence=0.0,
                          summary="检测结果不可用", raw=self._summary, available=False)
        metrics = self._summary.get("metrics", {})
        map50 = float(metrics.get("mAP50") or 0.0)
        reliability = max(0.0, min(1.0, map50))   # 模型可靠性先验

        dets = scene.get("detections", [])         # [{"cls":"pl40","conf":0.4}, ...]
        confs = [float(d.get("conf", 0.0)) for d in dets] or [0.0]
        min_conf = min(confs)
        risky = [d for d in dets if str(d.get("cls", "")).replace("tt100k_", "")
                 .startswith(_RISK_PREFIXES)]
        # 风险：检测到管控标志的比例 + 受模型可靠性调制
        density = len(risky) / max(1, len(dets))
        risk = max(0.0, min(1.0, 0.7 * density + 0.3 * reliability * bool(risky)))
        # 置信度：本次检测的最低框置信与模型可靠性的较小者
        confidence = round(min(min_conf if dets else reliability, reliability), 3)
        signs = ", ".join(self.tool.explain_class(d["cls"]) for d in dets[:3]) or "无标志"
        return Signal(
            self.name, risk=round(risk, 3), confidence=confidence,
            summary=(f"检测到 {len(dets)} 个标志(管控类 {len(risky)}); 模型 mAP50={map50} "
                     f"→ 风险 {risk:.2f}, 置信 {confidence:.2f}. {signs}"),
            raw={"scene_detections": dets, "model": self._summary})
