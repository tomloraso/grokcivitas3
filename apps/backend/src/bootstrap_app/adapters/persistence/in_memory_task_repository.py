from collections.abc import Sequence

from bootstrap_app.application.tasks.ports.task_repository import TaskRepository
from bootstrap_app.domain.tasks.models import Task


class InMemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._tasks: list[Task] = []

    def add(self, task: Task) -> Task:
        self._tasks.append(task)
        return task

    def list_all(self) -> Sequence[Task]:
        return list(self._tasks)
