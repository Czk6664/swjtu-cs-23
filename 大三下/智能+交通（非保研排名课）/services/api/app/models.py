from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowType(str, Enum):
    prediction_only = "prediction-only"
    detection_only = "detection-only"
    full_decision = "full-decision"


class TaskType(str, Enum):
    report = "report"
    voice = "voice"
    daily_summary = "daily-summary"


class TaskState(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    task_backend: str


class AnalyzeSceneRequest(BaseModel):
    workflow: WorkflowType = WorkflowType.full_decision
    scene_name: str = Field(min_length=1, max_length=120)
    include_report: bool = False
    include_voice: bool = False
    notes: str | None = None


class DecisionSummary(BaseModel):
    facts: list[str]
    risk_level: str
    recommendation: str
    explanation: str


class AnalyzeSceneResponse(BaseModel):
    result_id: str
    workflow: WorkflowType
    status: Literal["ready"]
    forecast: dict[str, Any] | None = None
    detection: dict[str, Any] | None = None
    decision: DecisionSummary | None = None
    spawned_tasks: list[str] = Field(default_factory=list)


class ResultEnvelope(BaseModel):
    result_id: str
    created_at: datetime
    payload: dict[str, Any]


class TaskCreateRequest(BaseModel):
    task_type: TaskType
    title: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskRecord(BaseModel):
    task_id: str
    task_type: TaskType
    title: str
    state: TaskState
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    error: str | None = None


class TaskCreateResponse(BaseModel):
    task_id: str
    state: TaskState

