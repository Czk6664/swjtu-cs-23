from app.dependencies import orchestration_service
from app.models import AnalyzeSceneRequest


def build_analysis_payload(request: AnalyzeSceneRequest) -> dict:
    return orchestration_service.analyze(request)
