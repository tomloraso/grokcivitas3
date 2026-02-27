from functools import lru_cache

from civitas.application.tasks.use_cases import CreateTaskUseCase, ListTasksUseCase
from civitas.infrastructure.persistence.in_memory_task_repository import InMemoryTaskRepository


@lru_cache(maxsize=1)
def task_repository() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


def create_task_use_case() -> CreateTaskUseCase:
    return CreateTaskUseCase(repo=task_repository())


def list_tasks_use_case() -> ListTasksUseCase:
    return ListTasksUseCase(repo=task_repository())
