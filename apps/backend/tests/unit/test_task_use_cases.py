from bootstrap_app.application.tasks.use_cases import CreateTaskUseCase, ListTasksUseCase
from bootstrap_app.domain.tasks.models import Task


class FakeTaskRepository:
    def __init__(self) -> None:
        self.tasks: list[Task] = []

    def add(self, task: Task) -> Task:
        self.tasks.append(task)
        return task

    def list_all(self) -> list[Task]:
        return list(self.tasks)


def test_create_and_list_tasks() -> None:
    repo = FakeTaskRepository()
    create_use_case = CreateTaskUseCase(repo=repo)
    list_use_case = ListTasksUseCase(repo=repo)

    created = create_use_case.execute("Ship bootstrap template")

    assert created.title == "Ship bootstrap template"
    tasks = list_use_case.execute()
    assert len(tasks) == 1
    assert tasks[0].id == created.id
