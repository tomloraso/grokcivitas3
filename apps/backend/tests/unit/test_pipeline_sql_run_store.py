from __future__ import annotations

from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from civitas.infrastructure.pipelines.base import PipelineSource
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
