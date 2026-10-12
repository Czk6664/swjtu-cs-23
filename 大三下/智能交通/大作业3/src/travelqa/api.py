"""FastAPI 接口 + 静态前端托管 —— 智能交通出行问答。

启动: python scripts/serve.py   (或 uvicorn travelqa.api:app)
接口:
  POST /api/ask   {query}     -> {intent, text, sources, tool_result}
  GET  /api/health
  GET  /                       -> 单文件前端 web/index.html
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .app import TravelQAApp
from .config import Config
from .router import extract_route_od
from .tools import DetectionTool, ForecastTool, route_plan, weather_query

WEB_DIR = Path(__file__).resolve().parents[2] / "web"

app = FastAPI(title="智能交通出行问答", version="0.1.0")
_qa: TravelQAApp | None = None
_cfg: Config | None = None


def _get_cfg() -> Config:
    global _cfg
    if _cfg is None:
        _cfg = Config.load()
    return _cfg


def _get_app() -> TravelQAApp:
    global _qa
    if _qa is None:
        _qa = TravelQAApp(_get_cfg())
    return _qa


class AskRequest(BaseModel):
    query: str


class WeatherRequest(BaseModel):
    city: str = "成都"
    date: str = "今天"


class RouteRequest(BaseModel):
    origin: str = ""
    destination: str = ""
    mode: str = "drive"
    query: str = ""


class ForecastRequest(BaseModel):
    dataset: str = "PEMS08"
    variant: str = "baseline"
    node_id: int = 0
    sample_index: int = -1


@app.get("/api/health")
def health() -> dict:
    qa = _get_app()
    return {"status": "ok", "kb_ready": qa.retriever.ready(),
            "llm_provider": qa.cfg.get("llm", "provider", default="offline")}


@app.post("/api/ask")
def ask(req: AskRequest) -> dict:
    try:
        qa = _get_app()
        ans = qa.ask(req.query)
        return asdict(ans)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "error": "问答服务暂时不可用",
                "detail": str(exc),
            },
        )


@app.post("/api/tools/weather")
def tool_weather(req: WeatherRequest) -> dict:
    return weather_query(_get_cfg(), city=req.city, date=req.date)


@app.post("/api/tools/route")
def tool_route(req: RouteRequest) -> dict:
    origin, destination = req.origin, req.destination
    if (not origin or not destination) and req.query:
        origin, destination = extract_route_od(req.query)
    return route_plan(_get_cfg(), origin, destination, mode=req.mode)


@app.post("/api/tools/forecast/summary")
def tool_forecast_summary(req: ForecastRequest) -> dict:
    return ForecastTool(_get_cfg()).summarize(dataset=req.dataset, variant=req.variant)


@app.post("/api/tools/forecast/predict")
def tool_forecast_predict(req: ForecastRequest) -> dict:
    return ForecastTool(_get_cfg()).predict(
        dataset=req.dataset,
        variant=req.variant,
        node_id=req.node_id,
        sample_index=req.sample_index,
    )


@app.post("/api/tools/detection/summary")
def tool_detection_summary() -> dict:
    return DetectionTool(_get_cfg()).summarize()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")
