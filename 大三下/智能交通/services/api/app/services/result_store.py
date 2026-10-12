from datetime import UTC, datetime
from uuid import uuid4

from app.models import ResultEnvelope


class InMemoryResultStore:
    def __init__(self) -> None:
        self._results: dict[str, ResultEnvelope] = {}

    def save(self, payload: dict) -> ResultEnvelope:
        result = ResultEnvelope(
            result_id=str(uuid4()),
            created_at=datetime.now(UTC),
            payload=payload,
        )
        self._results[result.result_id] = result
        return result

    def get(self, result_id: str) -> ResultEnvelope | None:
        return self._results.get(result_id)
