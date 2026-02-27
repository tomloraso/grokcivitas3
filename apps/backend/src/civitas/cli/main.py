import typer

from civitas.bootstrap.container import create_task_use_case, list_tasks_use_case

app = typer.Typer(help="Civitas CLI")


@app.command("create-task")
def create_task(title: str) -> None:
    use_case = create_task_use_case()
    task = use_case.execute(title=title)
    typer.echo(f"Created task {task.id}: {task.title}")


@app.command("list-tasks")
def list_tasks() -> None:
    use_case = list_tasks_use_case()
    for task in use_case.execute():
        typer.echo(f"{task.id} | {task.title} | {task.created_at.isoformat()}")
