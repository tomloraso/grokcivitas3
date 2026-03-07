from datetime import date
from uuid import UUID

import typer

from civitas.application.school_summaries.dto import SummaryGenerationResultDto
from civitas.bootstrap.container import (
    app_settings,
    create_task_use_case,
    data_quality_slo_check_use_case,
    get_school_analyst_use_case,
    get_school_overview_use_case,
    list_tasks_use_case,
    pipeline_runner,
    poll_school_analyst_batches_use_case,
    poll_school_overview_batches_use_case,
    submit_school_analyst_batches_use_case,
    submit_school_overview_batches_use_case,
)

app = typer.Typer(help="Civitas CLI")
pipeline_app = typer.Typer(help="Pipeline commands")
ops_app = typer.Typer(help="Operations commands")
data_quality_app = typer.Typer(help="Data quality commands")
GENERATE_SUMMARIES_URN_OPTION = typer.Option(None, "--urn")
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


@app.command("generate-summaries")
def generate_summaries(
    urn: list[str] | None = GENERATE_SUMMARIES_URN_OPTION,
    summary_type: str = typer.Option("all", "--type", case_sensitive=False),
    force: bool = typer.Option(False, "--force"),
    resume_run_id: str | None = typer.Option(None, "--resume-run-id"),
) -> None:
    if not app_settings().ai.enabled:
        typer.echo("AI generation is disabled. Set CIVITAS_AI_ENABLED=true to generate summaries.")
        raise typer.Exit(code=1)

    summary_kinds = _resolve_summary_kinds(summary_type)
    resolved_run_id: UUID | None = None
    if resume_run_id is not None:
        try:
            resolved_run_id = UUID(resume_run_id.strip())
        except ValueError as exc:
            raise typer.BadParameter("--resume-run-id must be a valid UUID.") from exc
    if resolved_run_id is not None and len(summary_kinds) > 1:
        raise typer.BadParameter("--resume-run-id requires --type overview or --type analyst.")

    has_failed = False
    for kind in summary_kinds:
        try:
            result = _submit_summary_use_case(kind).execute(
                urns=urn,
                trigger="manual",
                force=force,
                resume_run_id=resolved_run_id,
            )
        except RuntimeError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from None
        typer.echo(_format_summary_generation_result(kind, result))
        if result.generation_failed_count > 0 or result.validation_failed_count > 0:
            has_failed = True

    if has_failed:
        raise typer.Exit(code=1)


@app.command("poll-summary-batches")
def poll_summary_batches(
    run_id: str | None = typer.Option(None, "--run-id"),
    summary_type: str = typer.Option("all", "--type", case_sensitive=False),
) -> None:
    summary_kinds = _resolve_summary_kinds(summary_type)
    resolved_run_id: UUID | None = None
    if run_id is not None:
        try:
            resolved_run_id = UUID(run_id.strip())
        except ValueError as exc:
            raise typer.BadParameter("--run-id must be a valid UUID.") from exc
    if resolved_run_id is not None and len(summary_kinds) > 1:
        raise typer.BadParameter("--run-id requires --type overview or --type analyst.")

    had_pending = False
    has_failed = False
    for kind in summary_kinds:
        try:
            results = _poll_summary_use_case(kind).execute(run_id=resolved_run_id)
        except RuntimeError as exc:
            typer.echo(str(exc))
            raise typer.Exit(code=1) from None
        if not results:
            typer.echo(f"{kind}: no pending async batch items found.")
            continue

        had_pending = True
        for result in results:
            typer.echo(_format_summary_generation_result(kind, result))
            if result.generation_failed_count > 0 or result.validation_failed_count > 0:
                has_failed = True

    if not had_pending and len(summary_kinds) == 1:
        return

    if has_failed:
        raise typer.Exit(code=1)


@app.command("show-summary")
def show_summary(
    urn: str = typer.Option(..., "--urn"),
    summary_type: str = typer.Option("overview", "--type", case_sensitive=False),
) -> None:
    summary_kind = _resolve_single_summary_kind(summary_type)
    preview = _get_summary_use_case(summary_kind).execute(urn=urn)
    if preview is None:
        typer.echo(f"No {summary_kind} summary found for URN {urn}.")
        raise typer.Exit(code=1)

    typer.echo(
        f"{preview.summary_kind} | urn={preview.urn} | model={preview.model_id} "
        f"| prompt={preview.prompt_version} | generated_at={preview.generated_at.isoformat()}"
    )
    typer.echo("")
    typer.echo(preview.text)


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

    if not has_failed and normalized_source is None and app_settings().ai.enabled:
        has_failed = _run_pipeline_ai_generation()

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


def _run_pipeline_ai_generation() -> bool:
    has_failed = False
    for kind in ("overview", "analyst"):
        result = _submit_summary_use_case(kind).execute(trigger="pipeline")
        typer.echo(_format_summary_generation_result(f"ai[{kind}]", result))
        if result.generation_failed_count > 0 or result.validation_failed_count > 0:
            has_failed = True
    return has_failed


def _format_summary_generation_result(
    label: str,
    result: SummaryGenerationResultDto,
) -> str:
    return " ".join(
        [
            f"{label}: run_id={result.run_id}",
            f"status={result.status}",
            f"requested={result.requested_count}",
            f"pending={result.pending_count}",
            f"succeeded={result.succeeded_count}",
            f"generation_failed={result.generation_failed_count}",
            f"validation_failed={result.validation_failed_count}",
            f"skipped_current={result.skipped_current_count}",
        ]
    )


def _resolve_summary_kinds(summary_type: str) -> tuple[str, ...]:
    normalized = summary_type.strip().casefold()
    if normalized == "all":
        return ("overview", "analyst")
    if normalized in {"overview", "analyst"}:
        return (normalized,)
    raise typer.BadParameter("--type must be one of: overview, analyst, all.")


def _resolve_single_summary_kind(summary_type: str) -> str:
    summary_kinds = _resolve_summary_kinds(summary_type)
    if len(summary_kinds) != 1:
        raise typer.BadParameter("--type must be overview or analyst.")
    return summary_kinds[0]


def _get_summary_use_case(summary_kind: str):
    if summary_kind == "overview":
        return get_school_overview_use_case()
    return get_school_analyst_use_case()


def _submit_summary_use_case(summary_kind: str):
    if summary_kind == "overview":
        return submit_school_overview_batches_use_case()
    return submit_school_analyst_batches_use_case()


def _poll_summary_use_case(summary_kind: str):
    if summary_kind == "overview":
        return poll_school_overview_batches_use_case()
    return poll_school_analyst_batches_use_case()
