from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from civitas.infrastructure.pipelines.base import (
    PipelineResult,
    PipelineRunContext,
    PipelineRunStatus,
    PipelineSource,
)
from civitas.infrastructure.pipelines.runner import SqlPipelineRunStore


def _sqlite_store() -> SqlPipelineRunStore:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE pipeline_runs (
                    run_id text PRIMARY KEY
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE pipeline_source_locks (
                    source text PRIMARY KEY,
                    run_id text NOT NULL REFERENCES pipeline_runs(run_id),
                    acquired_at text NOT NULL
                )
                """
            )
        )
    return SqlPipelineRunStore(engine=engine)


def _sqlite_store_with_pipeline_runs() -> SqlPipelineRunStore:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE pipeline_runs (
                    run_id text PRIMARY KEY,
                    source text NOT NULL,
                    status text NOT NULL,
                    started_at text NOT NULL,
                    finished_at text NULL,
                    bronze_path text NOT NULL,
                    downloaded_rows integer NOT NULL DEFAULT 0,
                    staged_rows integer NOT NULL DEFAULT 0,
                    promoted_rows integer NOT NULL DEFAULT 0,
                    rejected_rows integer NOT NULL DEFAULT 0,
                    error_message text NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE app_cache_versions (
                    cache_key text PRIMARY KEY,
                    version_updated_at text NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE pipeline_source_locks (
                    source text PRIMARY KEY,
                    run_id text NOT NULL REFERENCES pipeline_runs(run_id),
                    acquired_at text NOT NULL
                )
                """
            )
        )
    return SqlPipelineRunStore(engine=engine)


def _context() -> PipelineRunContext:
    return PipelineRunContext(
        run_id=uuid4(),
        source=PipelineSource.GIAS,
        started_at=datetime(2026, 3, 4, 12, 0, tzinfo=timezone.utc),
        bronze_root=Path("data/bronze"),
    )


def _insert_started_run_row(store: SqlPipelineRunStore, context: PipelineRunContext) -> None:
    with store._engine.begin() as connection:  # noqa: SLF001 - test setup path
        connection.execute(
            text(
                """
                INSERT INTO pipeline_runs (
                    run_id,
                    source,
                    status,
                    started_at,
                    bronze_path,
                    downloaded_rows,
                    staged_rows,
                    promoted_rows,
                    rejected_rows
                ) VALUES (
                    :run_id,
                    :source,
                    :status,
                    :started_at,
                    :bronze_path,
                    0,
                    0,
                    0,
                    0
                )
                """
            ),
            {
                "run_id": str(context.run_id),
                "source": context.source.value,
                "status": PipelineRunStatus.RUNNING.value,
                "started_at": context.started_at.isoformat(),
                "bronze_path": str(context.bronze_source_path),
            },
        )


def test_acquire_source_lock_is_reentrant_for_same_run_id() -> None:
    store = _sqlite_store()
    run_id = uuid4()

    with store._engine.begin() as connection:  # noqa: SLF001 - test setup path
        connection.execute(
            text("INSERT INTO pipeline_runs (run_id) VALUES (:run_id)"),
            {"run_id": str(run_id)},
        )

    assert store.acquire_source_lock(source=PipelineSource.GIAS, run_id=run_id) is True
    assert store.acquire_source_lock(source=PipelineSource.GIAS, run_id=run_id) is True


def test_acquire_source_lock_blocks_different_run_id_for_same_source() -> None:
    store = _sqlite_store()
    first_run_id = uuid4()
    second_run_id = uuid4()

    with store._engine.begin() as connection:  # noqa: SLF001 - test setup path
        connection.execute(
            text("INSERT INTO pipeline_runs (run_id) VALUES (:run_id)"),
            [{"run_id": str(first_run_id)}, {"run_id": str(second_run_id)}],
        )

    assert store.acquire_source_lock(source=PipelineSource.GIAS, run_id=first_run_id) is True
    assert store.acquire_source_lock(source=PipelineSource.GIAS, run_id=second_run_id) is False


def test_record_finished_updates_school_profile_cache_version_on_success() -> None:
    store = _sqlite_store_with_pipeline_runs()
    context = _context()
    _insert_started_run_row(store, context)
    result = PipelineResult(
        status=PipelineRunStatus.SUCCEEDED,
        downloaded_rows=10,
        staged_rows=10,
        promoted_rows=10,
        rejected_rows=0,
    )

    store.record_finished(
        context=context,
        result=result,
        finished_at=datetime(2026, 3, 4, 12, 5, tzinfo=timezone.utc),
    )

    with store._engine.begin() as connection:  # noqa: SLF001 - assertion path
        row = connection.execute(
            text(
                """
                SELECT cache_key, version_updated_at
                FROM app_cache_versions
                WHERE cache_key = 'school_profile'
                """
            )
        ).fetchone()

    assert row is not None
    assert row[0] == "school_profile"
    assert row[1] is not None


def test_record_finished_does_not_update_school_profile_cache_version_on_failure() -> None:
    store = _sqlite_store_with_pipeline_runs()
    context = _context()
    _insert_started_run_row(store, context)
    result = PipelineResult(
        status=PipelineRunStatus.FAILED_QUALITY_GATE,
        downloaded_rows=10,
        staged_rows=5,
        promoted_rows=0,
        rejected_rows=5,
        error_message="gate failed",
    )

    store.record_finished(
        context=context,
        result=result,
        finished_at=datetime(2026, 3, 4, 12, 5, tzinfo=timezone.utc),
    )

    with store._engine.begin() as connection:  # noqa: SLF001 - assertion path
        row = connection.execute(
            text(
                """
                SELECT cache_key
                FROM app_cache_versions
                WHERE cache_key = 'school_profile'
                """
            )
        ).fetchone()

    assert row is None


def test_cleanup_orphaned_runs_marks_old_lockless_runs_failed() -> None:
    store = _sqlite_store_with_pipeline_runs()
    stale_run_id = str(uuid4())
    protected_run_id = str(uuid4())
    recent_run_id = str(uuid4())

    with store._engine.begin() as connection:  # noqa: SLF001 - test setup path
        connection.execute(
            text(
                """
                INSERT INTO pipeline_runs (
                    run_id,
                    source,
                    status,
                    started_at,
                    finished_at,
                    bronze_path,
                    downloaded_rows,
                    staged_rows,
                    promoted_rows,
                    rejected_rows,
                    error_message
                ) VALUES (
                    :run_id,
                    :source,
                    :status,
                    :started_at,
                    NULL,
                    :bronze_path,
                    0,
                    0,
                    0,
                    0,
                    NULL
                )
                """
            ),
            [
                {
                    "run_id": stale_run_id,
                    "source": PipelineSource.GIAS.value,
                    "status": PipelineRunStatus.RUNNING.value,
                    "started_at": "2026-03-04T12:00:00+00:00",
                    "bronze_path": "data/bronze/gias/2026-03-04",
                },
                {
                    "run_id": protected_run_id,
                    "source": PipelineSource.DFE_WORKFORCE.value,
                    "status": PipelineRunStatus.RUNNING.value,
                    "started_at": "2026-03-04T12:00:00+00:00",
                    "bronze_path": "data/bronze/dfe_workforce/2026-03-04",
                },
                {
                    "run_id": recent_run_id,
                    "source": PipelineSource.OFSTED_LATEST.value,
                    "status": PipelineRunStatus.RUNNING.value,
                    "started_at": "2026-03-10T11:30:00+00:00",
                    "bronze_path": "data/bronze/ofsted_latest/2026-03-10",
                },
            ],
        )
        connection.execute(
            text(
                """
                INSERT INTO pipeline_source_locks (source, run_id, acquired_at)
                VALUES (:source, :run_id, :acquired_at)
                """
            ),
            {
                "source": PipelineSource.DFE_WORKFORCE.value,
                "run_id": protected_run_id,
                "acquired_at": "2026-03-04T12:01:00+00:00",
            },
        )

    result = store.cleanup_orphaned_runs(
        started_before=datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
    )

    assert result.inspected_runs == 3
    assert result.cleaned_runs == 1
    assert result.cleaned_by_source == ((PipelineSource.GIAS.value, 1),)

    with store._engine.begin() as connection:  # noqa: SLF001 - assertion path
        stale_row = connection.execute(
            text(
                """
                SELECT status, finished_at, error_message
                FROM pipeline_runs
                WHERE run_id = :run_id
                """
            ),
            {"run_id": stale_run_id},
        ).one()
        protected_row = connection.execute(
            text(
                """
                SELECT status, finished_at
                FROM pipeline_runs
                WHERE run_id = :run_id
                """
            ),
            {"run_id": protected_run_id},
        ).one()

    assert stale_row[0] == PipelineRunStatus.FAILED.value
    assert stale_row[1] is not None
    assert stale_row[2] == "maintenance_id=orphaned_run_cleanup source=gias"
    assert protected_row[0] == PipelineRunStatus.RUNNING.value
    assert protected_row[1] is None


def test_cleanup_orphaned_runs_dry_run_leaves_rows_unchanged() -> None:
    store = _sqlite_store_with_pipeline_runs()
    stale_run_id = str(uuid4())

    with store._engine.begin() as connection:  # noqa: SLF001 - test setup path
        connection.execute(
            text(
                """
                INSERT INTO pipeline_runs (
                    run_id,
                    source,
                    status,
                    started_at,
                    finished_at,
                    bronze_path,
                    downloaded_rows,
                    staged_rows,
                    promoted_rows,
                    rejected_rows,
                    error_message
                ) VALUES (
                    :run_id,
                    :source,
                    :status,
                    :started_at,
                    NULL,
                    :bronze_path,
                    0,
                    0,
                    0,
                    0,
                    NULL
                )
                """
            ),
            {
                "run_id": stale_run_id,
                "source": PipelineSource.GIAS.value,
                "status": PipelineRunStatus.RUNNING.value,
                "started_at": "2026-03-04T12:00:00+00:00",
                "bronze_path": "data/bronze/gias/2026-03-04",
            },
        )

    result = store.cleanup_orphaned_runs(
        started_before=datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
        dry_run=True,
    )

    assert result.cleaned_runs == 1

    with store._engine.begin() as connection:  # noqa: SLF001 - assertion path
        row = connection.execute(
            text(
                """
                SELECT status, finished_at, error_message
                FROM pipeline_runs
                WHERE run_id = :run_id
                """
            ),
            {"run_id": stale_run_id},
        ).one()

    assert row[0] == PipelineRunStatus.RUNNING.value
    assert row[1] is None
    assert row[2] is None
