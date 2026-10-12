from typing import Any

from app.models import AnalyzeSceneRequest
from app.services.decision_service import DecisionService
from app.services.detection_service import DetectionService
from app.services.forecast_service import ForecastService


class OrchestrationService:
    def __init__(
        self,
        forecast_service: ForecastService,
        detection_service: DetectionService,
        decision_service: DecisionService,
    ) -> None:
        self.forecast_service = forecast_service
        self.detection_service = detection_service
        self.decision_service = decision_service

    def analyze(self, request: AnalyzeSceneRequest) -> dict[str, Any]:
        forecast = self.forecast_service.summarize() if request.workflow != "detection-only" else None
        detection = self.detection_service.summarize() if request.workflow != "prediction-only" else None
        decision = self.decision_service.generate(
            scene_name=request.scene_name,
            workflow=request.workflow.value,
            notes=request.notes,
            has_forecast=forecast is not None,
            has_detection=detection is not None,
        )

        return {
            "scene_name": request.scene_name,
            "workflow": request.workflow.value,
            "forecast": forecast,
            "detection": detection,
            "decision": decision.model_dump(),
        }
