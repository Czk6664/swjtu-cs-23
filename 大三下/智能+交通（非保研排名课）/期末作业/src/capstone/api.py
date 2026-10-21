"""FastAPI 接口 + 静态前端 —— 智能交通管理决策系统（决策融合 + 数据飞轮）。

启动: python scripts/serve.py   (或 uvicorn capstone.api:app)
接口:
  POST /api/decide          {scene}                 -> 决策结果(风险/动作/归因/解释)
  POST /api/flywheel/seed    {model, n}             -> 灌入难例遥测(演示用)
  POST /api/flywheel/round   {model, inject_regression} -> 一轮飞轮(门控晋升/保留)
  GET  /api/registry/{model}                         -> 版本/生产指针/指标曲线
  GET  /api/health
  GET  /                                             -> web/index.html
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import Config
from .flywheel import TelemetryCollector
from .pipeline import TrafficDecisionSystem

WEB_DIR = Path(__file__).resolve().parents[2] / "web"

app = FastAPI(title="智能交通管理决策系统", version="0.1.0")
_sys: TrafficDecisionSystem | None = None


def _system() -> TrafficDecisionSystem:
    global _sys
    if _sys is None:
        _sys = TrafficDecisionSystem(Config.load())
    return _sys


class Scene(BaseModel):
    scene_id: str = "scene"
    workflow: str | None = None
    traffic_load: float | None = None
    forecast_dataset: str = "PEMS08"
    detections: list[dict] = []
    query: str | None = None


class FlywheelReq(BaseModel):
    model: str = "detection"
    inject_regression: bool = False


class SeedReq(BaseModel):
    model: str = "detection"
    n: int = 8


@app.get("/api/health")
def health() -> dict:
    s = _system()
    return {"status": "ok",
            "models": {m: s.registry.production_version(m) for m in ("detection", "forecast")}}


@app.post("/api/decide")
def decide(scene: Scene) -> dict:
    s = _system()
    payload = {k: v for k, v in scene.model_dump().items() if v is not None}
    return asdict(s.decision_flow(payload))


@app.post("/api/flywheel/seed")
def seed(req: SeedReq) -> dict:
    s = _system()
    col = TelemetryCollector(s.cfg.data_path("telemetry"))
    for i in range(req.n):
        col.log(model_name=req.model, model_version="v1",
                output={"cls": "pl100", "conf": 0.18}, confidence=0.18,
                input_ref=f"seed-{i}", flagged_reason="low_confidence(<0.35)")
    return {"seeded": req.n, "model": req.model}


@app.post("/api/flywheel/round")
def flywheel_round(req: FlywheelReq) -> dict:
    s = _system()
    return s.flywheel_round(req.model, inject_regression=req.inject_regression)


@app.get("/api/registry/{model}")
def registry(model: str) -> dict:
    s = _system()
    versions = s.registry.list_versions(model)
    primary = "mAP50" if model == "detection" else "mae"
    curve = [{"version": v, "metric": d["metrics"].get(primary), "status": d["status"]}
             for v, d in versions.items()]
    return {"model": model, "primary": primary,
            "production": s.registry.production_version(model), "curve": curve}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")
