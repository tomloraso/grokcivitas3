from collections.abc import Sequence

from civitas.application.tasks.ports.task_repository import TaskRepository
from civitas.domain.tasks.models import Task


class CreateTaskUseCase:
    def __init__(self, repo: TaskRepository) -> None:
        self._repo = repo

    def execute(self, title: str) -> Task:
        task = Task.create(title=title)
        return self._repo.add(task)


class ListTasksUseCase:
    def __init__(self, repo: TaskRepository) -> None:
        self._repo = repo

    def execute(self) -> Sequence[Task]:
        return self._repo.list_all()
