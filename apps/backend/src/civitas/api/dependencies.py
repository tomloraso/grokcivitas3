from civitas.application.tasks.use_cases import CreateTaskUseCase, ListTasksUseCase
from civitas.bootstrap.container import create_task_use_case, list_tasks_use_case


def get_create_task_use_case() -> CreateTaskUseCase:
    return create_task_use_case()


def get_list_tasks_use_case() -> ListTasksUseCase:
    return list_tasks_use_case()
