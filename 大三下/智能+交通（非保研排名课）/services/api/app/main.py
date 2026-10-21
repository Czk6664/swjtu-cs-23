from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse

from app.config import settings
from app.dependencies import hermes_adapter, result_store, task_manager
from app.models import (
    AnalyzeSceneRequest,
    AnalyzeSceneResponse,
    HealthResponse,
    TaskCreateRequest,
    TaskCreateResponse,
    TaskRecord,
)
from app.services.workflow import build_analysis_payload


app = FastAPI(title="Traffic Decision API", version="0.1.0")


@app.on_event("startup")
async def validate_runtime_dependencies() -> None:
    hermes_adapter.validate_environment()


@app.get("/", response_class=HTMLResponse)
async def root_page() -> str:
    return """
    <html lang="zh-CN">
      <head><meta charset="utf-8"><title>Traffic Decision API</title></head>
      <body style="font-family:Segoe UI,Microsoft YaHei UI,sans-serif;padding:32px;">
        <h1>Traffic Decision API</h1>
        <p>后端服务已经启动。</p>
        <p>前端页面请访问 <a href="http://127.0.0.1:5173">http://127.0.0.1:5173</a></p>
        <p>接口文档请访问 <a href="/docs">/docs</a></p>
      </body>
    </html>
    """


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name, task_backend=settings.task_backend)


@app.post("/api/analyze-scene", response_model=AnalyzeSceneResponse)
async def analyze_scene(request: AnalyzeSceneRequest) -> AnalyzeSceneResponse:
    payload = build_analysis_payload(request)
    result = result_store.save(payload)
    spawned_tasks: list[str] = []

    if request.include_report:
        task = await task_manager.enqueue(
            TaskCreateRequest(
                task_type="report",
                title=f"{request.scene_name} report",
                payload={"result_id": result.result_id, "scene_name": request.scene_name},
            ),
            hermes_adapter.run_task,
        )
        spawned_tasks.append(task.task_id)

    if request.include_voice:
        task = await task_manager.enqueue(
            TaskCreateRequest(
                task_type="voice",
                title=f"{request.scene_name} voice briefing",
                payload={"result_id": result.result_id, "scene_name": request.scene_name},
            ),
            hermes_adapter.run_task,
        )
        spawned_tasks.append(task.task_id)

    return AnalyzeSceneResponse(
        result_id=result.result_id,
        workflow=request.workflow,
        status="ready",
        forecast=payload.get("forecast"),
        detection=payload.get("detection"),
        decision=payload.get("decision"),
        spawned_tasks=spawned_tasks,
    )


@app.get("/api/results/{result_id}")
async def get_result(result_id: str):
    result = result_store.get(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@app.post("/api/tasks", response_model=TaskCreateResponse)
async def create_task(request: TaskCreateRequest) -> TaskCreateResponse:
    task = await task_manager.enqueue(request, hermes_adapter.run_task)
    return TaskCreateResponse(task_id=task.task_id, state=task.state)


@app.get("/api/tasks")
async def list_tasks() -> list[TaskRecord]:
    return task_manager.list_tasks()


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str) -> TaskRecord:
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/assets/detection/{asset_name}")
async def get_detection_asset(asset_name: str):
    allowed = {"val_batch0_pred.jpg", "confusion_matrix_normalized.png", "results.png"}
    if asset_name not in allowed:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset_path = Path(settings.traffic_detection_run_dir) / asset_name
    if not asset_path.exists():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(asset_path)
