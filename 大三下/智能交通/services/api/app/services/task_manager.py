import asyncio
from datetime import UTC, datetime
from typing import Awaitable, Callable
from uuid import uuid4

from app.models import TaskCreateRequest, TaskRecord, TaskState


TaskRunner = Callable[[TaskRecord], Awaitable[dict]]


class InMemoryTaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}

    def list_tasks(self) -> list[TaskRecord]:
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    async def enqueue(self, request: TaskCreateRequest, runner: TaskRunner) -> TaskRecord:
        record = TaskRecord(
            task_id=str(uuid4()),
            task_type=request.task_type,
            title=request.title,
            state=TaskState.queued,
            payload=request.payload,
        )
        self._tasks[record.task_id] = record
        asyncio.create_task(self._run(record.task_id, runner))
        return record

    async def _run(self, task_id: str, runner: TaskRunner) -> None:
        task = self._tasks[task_id]
        task.state = TaskState.running
        task.updated_at = datetime.now(UTC)
        try:
          result = await runner(task)
          task.result = result
          task.state = TaskState.succeeded
        except Exception as exc:  # noqa: BLE001
          task.error = str(exc)
          task.state = TaskState.failed
        finally:
          task.updated_at = datetime.now(UTC)
