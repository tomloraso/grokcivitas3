from functools import lru_cache

from civitas.adapters.persistence.in_memory_task_repository import InMemoryTaskRepository
from civitas.application.tasks.use_cases import CreateTaskUseCase, ListTasksUseCase


@lru_cache(maxsize=1)
def _repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


def get_create_task_use_case() -> CreateTaskUseCase:
    return CreateTaskUseCase(repo=_repo())


def get_list_tasks_use_case() -> ListTasksUseCase:
    return ListTasksUseCase(repo=_repo())
