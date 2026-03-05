from datetime import date
from uuid import UUID

import typer

from civitas.bootstrap.container import (
    create_task_use_case,
    data_quality_slo_check_use_case,
    list_tasks_use_case,
    pipeline_runner,
)

app = typer.Typer(help="Civitas CLI")
pipeline_app = typer.Typer(help="Pipeline commands")
ops_app = typer.Typer(help="Operations commands")
data_quality_app = typer.Typer(help="Data quality commands")
app.add_typer(pipeline_app, name="pipeline")
app.add_typer(ops_app, name="ops")
ops_app.add_typer(data_quality_app, name="data-quality")


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
    resume: bool = typer.Option(False, "--resume"),
    force_refresh: bool = typer.Option(False, "--force-refresh"),
) -> None:
    normalized_source = source.strip().lower() if source is not None else None

    if normalized_source is None and not run_all:
        raise typer.BadParameter("Either --source or --all must be provided.")
    if normalized_source is not None and run_all:
        raise typer.BadParameter("Use either --source or --all, not both.")
    if resume and run_all:
        raise typer.BadParameter("--resume can only be used with --source.")
    if resume and force_refresh:
        raise typer.BadParameter("--force-refresh cannot be used with --resume.")

    runner = pipeline_runner()
    available_sources = set(runner.available_sources())
    if normalized_source is not None and normalized_source not in available_sources:
        available = ", ".join(sorted(available_sources))
        raise typer.BadParameter(
            f"Unsupported source '{normalized_source}'. Expected one of: {available}."
        )

    if normalized_source is not None:
        results = {
            normalized_source: runner.run_source(
                normalized_source,
                resume=resume,
                force_refresh=force_refresh,
            )
        }
    else:
        results = {
            result_source.value: result
            for result_source, result in runner.run_all(force_refresh=force_refresh).items()
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
        if result.status.is_hard_failure():
            has_failed = True

    if has_failed:
        raise typer.Exit(code=1)


@pipeline_app.command("resume")
def resume_pipeline(run_id: str = typer.Option(..., "--run-id")) -> None:
    try:
        resolved_run_id = str(UUID(run_id.strip()))
    except ValueError as exc:
        raise typer.BadParameter("--run-id must be a valid UUID.") from exc

    runner = pipeline_runner()
    result_source, result = runner.resume_run(resolved_run_id)

    typer.echo(
        f"{result_source.value}: {result.status.value} "
        f"(downloaded={result.downloaded_rows}, staged={result.staged_rows}, "
        f"promoted={result.promoted_rows}, rejected={result.rejected_rows})"
    )
    if result.error_message:
        typer.echo(f"  error: {result.error_message}")
    if result.status.is_hard_failure():
        raise typer.Exit(code=1)


@data_quality_app.command("snapshot")
def snapshot_data_quality(
    strict: bool = typer.Option(False, "--strict"),
    snapshot_date: str | None = typer.Option(None, "--snapshot-date"),
) -> None:
    resolved_snapshot_date: date | None = None
    if snapshot_date is not None:
        try:
            resolved_snapshot_date = date.fromisoformat(snapshot_date.strip())
        except ValueError as exc:
            raise typer.BadParameter("--snapshot-date must be in YYYY-MM-DD format.") from exc

    use_case = data_quality_slo_check_use_case()
    report = use_case.execute(snapshot_date=resolved_snapshot_date)

    typer.echo(f"snapshot_date={report.snapshot_date.isoformat()}")
    for snapshot in report.snapshots:
        source_lag_text = (
            "n/a"
            if snapshot.source_freshness_lag_hours is None
            else f"{snapshot.source_freshness_lag_hours:.2f}h"
        )
        section_lag_text = (
            "n/a"
            if snapshot.section_freshness_lag_hours is None
            else f"{snapshot.section_freshness_lag_hours:.2f}h"
        )
        typer.echo(
            f"{snapshot.source}/{snapshot.section}: "
            f"coverage={snapshot.section_coverage_ratio:.4f} "
            f"({snapshot.schools_with_section_count}/{snapshot.schools_total_count}) "
            f"source_lag={source_lag_text} section_lag={section_lag_text}"
        )

    for run_health in report.run_health:
        typer.echo(
            f"run_health[{run_health.source}]: "
            f"quality_gate_failures_total={run_health.quality_gate_failures_total} "
            f"consecutive_failed_runs={run_health.consecutive_failed_runs}"
        )

    if report.alerts:
        typer.echo("alerts:")
        for alert in report.alerts:
            source_text = alert.source or "-"
            section_text = alert.section or "-"
            observed_text = "n/a" if alert.observed_value is None else str(alert.observed_value)
            threshold_text = "n/a" if alert.threshold_value is None else str(alert.threshold_value)
            typer.echo(
                f"  [{alert.severity}] {alert.alert_type} "
                f"source={source_text} section={section_text} "
                f"observed={observed_text} threshold={threshold_text} "
                f"message={alert.message}"
            )
    else:
        typer.echo("alerts: none")

    blocking_alerts = tuple(alert for alert in report.alerts if alert.severity == "critical")
    if strict and blocking_alerts:
        raise typer.Exit(code=1)
