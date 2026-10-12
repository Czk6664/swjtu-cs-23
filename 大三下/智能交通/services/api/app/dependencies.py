from app.services.hermes import HermesAdapter
from app.services.detection_service import DetectionService
from app.services.decision_service import DecisionService
from app.services.forecast_service import ForecastService
from app.services.orchestration_service import OrchestrationService
from app.services.result_store import InMemoryResultStore
from app.services.task_manager import InMemoryTaskManager


result_store = InMemoryResultStore()
task_manager = InMemoryTaskManager()
hermes_adapter = HermesAdapter()
forecast_service = ForecastService()
detection_service = DetectionService()
decision_service = DecisionService()
orchestration_service = OrchestrationService(
    forecast_service=forecast_service,
    detection_service=detection_service,
    decision_service=decision_service,
)
