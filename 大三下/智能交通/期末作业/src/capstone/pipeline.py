"""端到端编排器：把三个大作业整合为一个完整系统。

decision_flow(scene)  : 一次决策请求 —— 路由→小模型推理→采集遥测→融合→决策与解释。
flywheel_round(model) : 一轮飞轮 —— 挖掘→标注→重训(模拟)→门控→晋升/保留。

二者共享同一个遥测库与模型注册表，构成"用得越多、数据越多、模型越好"的闭环。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from .config import Config
from .flywheel import (ModelRegistry, TelemetryCollector, evaluate_candidate,
                       label_snapshot, mine_hard_cases, retrain_candidate)
from .models import DetectionAdapter, DialogRagAdapter, ForecastAdapter
from .orchestration import decide, fuse, route


@dataclass
class DecisionResult:
    scene_id: str
    risk_level: str
    risk_score: float
    action: str
    rationale: str
    explanation: str
    contributions: list = field(default_factory=list)
    disagreements: list = field(default_factory=list)


class TrafficDecisionSystem:
    def __init__(self, cfg: Config | None = None):
        self.cfg = cfg or Config.load()
        self.adapters = {
            "forecast": ForecastAdapter(self.cfg),
            "detection": DetectionAdapter(self.cfg),
            "dialog_rag": DialogRagAdapter(self.cfg),
        }
        self.collector = TelemetryCollector(self.cfg.data_path("telemetry"))
        self.registry = ModelRegistry(self.cfg.data_path("registry", "models.json"))
        self._ensure_baseline_registry()

    # === 决策流 ==========================================================
    def decision_flow(self, scene: dict) -> DecisionResult:
        selected = route(scene)
        signals = []
        for name in selected:
            sig = self.adapters[name].infer(scene)
            signals.append(sig)

        assess = fuse(signals, self.cfg)
        decision = decide(assess, self.cfg, dialog_adapter=self.adapters.get("dialog_rag"))

        # 采集遥测（每个小模型一行），分歧/低置信写入 flagged_reason
        verdict = {"risk_level": decision.risk_level, "risk_score": decision.risk_score,
                   "disagreements": decision.disagreements}
        dis_signals = {d["signal"] for d in decision.disagreements}
        for sig in signals:
            if not sig.available:
                continue
            self.collector.log(
                model_name=sig.name,
                model_version=self.registry.production_version(sig.name) or "v1",
                output=sig.raw, confidence=sig.confidence,
                input_ref=scene.get("scene_id", ""),
                big_model_verdict=verdict,
                flagged_reason=("model_disagreement" if sig.name in dis_signals else ""))

        return DecisionResult(
            scene_id=scene.get("scene_id", ""), risk_level=decision.risk_level,
            risk_score=decision.risk_score, action=decision.action,
            rationale=decision.rationale, explanation=decision.explanation,
            contributions=assess.contributions, disagreements=decision.disagreements)

    # === 飞轮 ============================================================
    def flywheel_round(self, model_name: str, inject_regression: bool = False) -> dict:
        telemetry = self.collector.read_all(model_name)
        hard = mine_hard_cases(telemetry, self.cfg, model_name)
        min_n = self.cfg.get("flywheel", "mining", "min_hard_cases_to_retrain", default=5)

        report = {"model": model_name, "telemetry": len(telemetry),
                  "hard_cases": len(hard), "min_to_retrain": min_n}
        if len(hard) < min_n:
            report["status"] = "skip"
            report["note"] = f"难例 {len(hard)} < 阈值 {min_n}，本轮不重训。"
            return report

        prod_ver = self.registry.production_version(model_name) or "v1"
        next_ver = _next_version(prod_ver)
        snapshots_dir = self.cfg.data_path("snapshots")
        manifest = label_snapshot(hard, snapshots_dir, model_name, next_ver)

        base = self.registry.list_versions(model_name).get(prod_ver, {}).get("metrics", {})
        candidate = retrain_candidate(model_name, base, len(hard), next_ver,
                                      inject_regression=inject_regression)
        gate = evaluate_candidate(model_name, candidate["metrics"],
                                  base, self.cfg)

        self.registry.register(model_name, next_ver, candidate["checkpoint"],
                               manifest["version"], candidate["metrics"], status="staging")
        if gate.passed:
            old = self.registry.promote(model_name, next_ver)
            report.update(status="promoted", promoted_to=next_ver, archived=old)
        else:
            report.update(status="rejected", kept=prod_ver)

        report.update({
            "snapshot": manifest, "candidate_metrics": candidate["metrics"],
            "gate": {"passed": gate.passed, "metric": gate.primary_metric,
                     "production": gate.production_value, "candidate": gate.candidate_value,
                     "gain": gate.gain, "reason": gate.reason},
        })
        return report

    # === 初始化基线注册表（用大作业2 真实 mAP / 大作业1 真实 mae） ========
    def _ensure_baseline_registry(self) -> None:
        if self.registry.production_version("detection") is None:
            det = self.adapters["detection"]._summary.get("metrics", {})
            self.registry.register("detection", "v1", "大作业2/exp_C.../best.pt",
                                   "baseline", {"mAP50": det.get("mAP50", 0.758)},
                                   status="production")
        if self.registry.production_version("forecast") is None:
            fc = self.adapters["forecast"].tool.summarize(dataset="PEMS08")
            mae = (fc.get("overall", {}) or {}).get("mae", 13.706)
            self.registry.register("forecast", "v1", "大作业1/results/baseline.pth",
                                   "baseline", {"mae": mae}, status="production")


def _next_version(ver: str) -> str:
    try:
        return f"v{int(ver.lstrip('v')) + 1}"
    except ValueError:
        return "v2"


def to_json(obj) -> str:
    return json.dumps(asdict(obj) if hasattr(obj, "__dataclass_fields__") else obj,
                      ensure_ascii=False, indent=2)
