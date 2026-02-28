import typer

from civitas.bootstrap.container import (
    create_task_use_case,
    list_tasks_use_case,
    pipeline_runner,
)

app = typer.Typer(help="Civitas CLI")
pipeline_app = typer.Typer(help="Pipeline commands")
app.add_typer(pipeline_app, name="pipeline")


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


@pipeline_app.command("run")
def run_pipeline(
    source: str | None = typer.Option(None, "--source", case_sensitive=False),
    run_all: bool = typer.Option(False, "--all"),
) -> None:
    normalized_source = source.strip().lower() if source is not None else None

    if normalized_source is None and not run_all:
        raise typer.BadParameter("Either --source or --all must be provided.")
    if normalized_source is not None and run_all:
        raise typer.BadParameter("Use either --source or --all, not both.")

    runner = pipeline_runner()
    available_sources = set(runner.available_sources())
    if normalized_source is not None and normalized_source not in available_sources:
        available = ", ".join(sorted(available_sources))
        raise typer.BadParameter(
            f"Unsupported source '{normalized_source}'. Expected one of: {available}."
        )

    if normalized_source is not None:
        results = {normalized_source: runner.run_source(normalized_source)}
    else:
        results = {
            result_source.value: result for result_source, result in runner.run_all().items()
        }

    has_failed = False
    for result_source, result in results.items():
        typer.echo(
            f"{result_source}: {result.status.value} "
            f"(downloaded={result.downloaded_rows}, staged={result.staged_rows}, "
            f"promoted={result.promoted_rows}, rejected={result.rejected_rows})"
        )
        if result.error_message:
            typer.echo(f"  error: {result.error_message}")
        if result.status.value == "failed":
            has_failed = True

    if has_failed:
        raise typer.Exit(code=1)
