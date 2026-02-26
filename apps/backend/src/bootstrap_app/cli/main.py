import typer

from bootstrap_app.adapters.persistence.in_memory_task_repository import InMemoryTaskRepository
from bootstrap_app.application.tasks.use_cases import CreateTaskUseCase, ListTasksUseCase

app = typer.Typer(help="Bootstrap App CLI")
_repo = InMemoryTaskRepository()


@app.command("create-task")
def create_task(title: str) -> None:
    use_case = CreateTaskUseCase(repo=_repo)
    task = use_case.execute(title=title)
    typer.echo(f"Created task {task.id}: {task.title}")


@app.command("list-tasks")
def list_tasks() -> None:
    use_case = ListTasksUseCase(repo=_repo)
    for task in use_case.execute():
        typer.echo(f"{task.id} | {task.title} | {task.created_at.isoformat()}")
