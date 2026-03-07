from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine

from civitas.domain.school_summaries.models import SchoolSummary, SummaryGenerationRunItem
from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_summary_repository import PostgresSummaryRepository


def _database_url() -> str:
    return AppSettings().database.url


def _build_engine(database_url: str, schema_name: str | None = None) -> Engine:
    if database_url.startswith("postgresql"):
        engine = create_engine(database_url, future=True, connect_args={"connect_timeout": 2})
    else:
        engine = create_engine(database_url, future=True)
    if schema_name is not None and database_url.startswith("postgresql"):

        @event.listens_for(engine, "connect")
        def _set_search_path(dbapi_connection, _connection_record) -> None:  # type: ignore[no-redef]
            with dbapi_connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema_name}"')

    return engine


def _database_available(database_url: str) -> bool:
    engine = _build_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


DATABASE_URL = _database_url()
DATABASE_AVAILABLE = _database_available(DATABASE_URL)
pytestmark = pytest.mark.skipif(
    not DATABASE_AVAILABLE,
    reason="Postgres database unavailable for summary repository integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    schema_name = f"test_summary_repository_{uuid4().hex}"
    admin_engine = _build_engine(DATABASE_URL)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    admin_engine.dispose()

    engine = _build_engine(DATABASE_URL, schema_name=schema_name)
    _ensure_schema(engine)
    _cleanup(engine)
    _seed(engine)
    try:
        yield engine
    finally:
        _cleanup(engine)
        engine.dispose()
        admin_engine = _build_engine(DATABASE_URL)
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        admin_engine.dispose()


def _ensure_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schools (
                    urn text PRIMARY KEY,
                    name text NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_ai_summaries (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    summary_kind text NOT NULL,
                    text text NOT NULL,
                    data_version_hash text NOT NULL,
                    prompt_version text NOT NULL,
                    model_id text NOT NULL,
                    generated_at timestamptz NOT NULL,
                    generation_duration_ms integer NULL,
                    PRIMARY KEY (urn, summary_kind)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_ai_summary_history (
                    id uuid PRIMARY KEY,
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    summary_kind text NOT NULL,
                    text text NOT NULL,
                    data_version_hash text NOT NULL,
                    prompt_version text NOT NULL,
                    model_id text NOT NULL,
                    generated_at timestamptz NOT NULL,
                    superseded_at timestamptz NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ai_generation_runs (
                    id uuid PRIMARY KEY,
                    summary_kind text NOT NULL,
                    trigger text NOT NULL,
                    requested_count integer NOT NULL,
                    succeeded_count integer NOT NULL DEFAULT 0,
                    generation_failed_count integer NOT NULL DEFAULT 0,
                    validation_failed_count integer NOT NULL DEFAULT 0,
                    started_at timestamptz NOT NULL,
                    completed_at timestamptz NULL,
                    status text NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ai_generation_run_items (
                    run_id uuid NOT NULL REFERENCES ai_generation_runs(id) ON DELETE CASCADE,
                    urn text NOT NULL,
                    status text NOT NULL,
                    attempt_count integer NOT NULL DEFAULT 0,
                    failure_reason_codes text[] NULL,
                    completed_at timestamptz NULL,
                    data_version_hash text NULL,
                    provider_name text NULL,
                    provider_batch_id text NULL,
                    prompt_version text NULL,
                    submitted_at timestamptz NULL,
                    PRIMARY KEY (run_id, urn)
                )
                """
            )
        )


def _seed(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn,
                    name
                ) VALUES (
                    '920001',
                    'Summary Test School'
                )
                """
            ),
        )


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM ai_generation_run_items"))
        connection.execute(text("DELETE FROM ai_generation_runs"))
        connection.execute(text("DELETE FROM school_ai_summary_history"))
        connection.execute(text("DELETE FROM school_ai_summaries"))
        connection.execute(text("DELETE FROM schools WHERE urn = '920001'"))


def test_summary_repository_upserts_and_archives_history(engine: Engine) -> None:
    repository = PostgresSummaryRepository(engine=engine)
    first = SchoolSummary(
        urn="920001",
        summary_kind="overview",
        text="Initial overview.",
        data_version_hash="hash-1",
        prompt_version="overview.v1",
        model_id="grok-test",
        generated_at=datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc),
        generation_duration_ms=120,
    )
    second = SchoolSummary(
        urn="920001",
        summary_kind="overview",
        text="Updated overview.",
        data_version_hash="hash-2",
        prompt_version="overview.v2",
        model_id="grok-test",
        generated_at=datetime(2026, 3, 5, 13, 0, tzinfo=timezone.utc),
        generation_duration_ms=140,
    )

    repository.upsert_summary(first)
    repository.upsert_summary(second)

    loaded = repository.get_summary("920001", "overview")
    assert loaded is not None
    assert loaded.text == "Updated overview."
    assert loaded.data_version_hash == "hash-2"

    with engine.connect() as connection:
        history_rows = connection.execute(
            text(
                """
                SELECT text, prompt_version, summary_kind
                FROM school_ai_summary_history
                WHERE urn = '920001'
                """
            )
        ).fetchall()

    assert len(history_rows) == 1
    assert history_rows[0][0] == "Initial overview."
    assert history_rows[0][1] == "overview.v1"
    assert history_rows[0][2] == "overview"


def test_summary_repository_keeps_overview_and_analyst_rows_separate(engine: Engine) -> None:
    repository = PostgresSummaryRepository(engine=engine)
    repository.upsert_summary(
        SchoolSummary(
            urn="920001",
            summary_kind="overview",
            text="Overview text.",
            data_version_hash="overview-hash",
            prompt_version="overview.v1",
            model_id="grok-test",
            generated_at=datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc),
            generation_duration_ms=120,
        )
    )
    repository.upsert_summary(
        SchoolSummary(
            urn="920001",
            summary_kind="analyst",
            text="Analyst text.",
            data_version_hash="analyst-hash",
            prompt_version="analyst.v1",
            model_id="grok-test",
            generated_at=datetime(2026, 3, 5, 12, 5, tzinfo=timezone.utc),
            generation_duration_ms=140,
        )
    )

    overview = repository.get_summary("920001", "overview")
    analyst = repository.get_summary("920001", "analyst")

    assert overview is not None
    assert analyst is not None
    assert overview.text == "Overview text."
    assert analyst.text == "Analyst text."


def test_summary_repository_tracks_generation_runs(engine: Engine) -> None:
    repository = PostgresSummaryRepository(engine=engine)

    run = repository.create_run(trigger="manual", requested_count=2, summary_kind="overview")
    repository.upsert_run_item(
        item=_run_item(run.id, "920001", "succeeded", (), 1),
    )
    repository.upsert_run_item(
        item=_run_item(run.id, "920002", "validation_failed", ("word_count_too_short",), 2),
    )

    finalized = repository.finalize_run(run.id, "partial")
    items = repository.list_run_items(run.id)

    assert finalized.succeeded_count == 1
    assert finalized.validation_failed_count == 1
    assert finalized.status == "partial"
    assert finalized.summary_kind == "overview"
    assert len(items) == 2
    assert items[1].failure_reason_codes == ("word_count_too_short",)


def test_summary_repository_bulk_upserts_run_items(engine: Engine) -> None:
    repository = PostgresSummaryRepository(engine=engine)
    run = repository.create_run(trigger="manual", requested_count=2, summary_kind="overview")

    repository.upsert_run_items(
        [
            SummaryGenerationRunItem(
                run_id=run.id,
                urn="920001",
                status="submitted_batch",
                attempt_count=1,
                failure_reason_codes=(),
                completed_at=None,
                data_version_hash="hash-1",
                provider_name="grok",
                provider_batch_id="batch-1",
                prompt_version="overview.v1",
                submitted_at=datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc),
            ),
            SummaryGenerationRunItem(
                run_id=run.id,
                urn="920002",
                status="generation_failed",
                attempt_count=1,
                failure_reason_codes=("provider_error",),
                completed_at=datetime(2026, 3, 5, 12, 5, tzinfo=timezone.utc),
                data_version_hash="hash-2",
            ),
        ]
    )

    items = sorted(repository.list_run_items(run.id), key=lambda item: item.urn)

    assert [item.urn for item in items] == ["920001", "920002"]
    assert items[0].provider_batch_id == "batch-1"
    assert items[1].failure_reason_codes == ("provider_error",)


def test_summary_repository_lists_pending_batch_items(engine: Engine) -> None:
    repository = PostgresSummaryRepository(engine=engine)
    run = repository.create_run(trigger="manual", requested_count=1, summary_kind="overview")
    repository.upsert_run_item(
        item=SummaryGenerationRunItem(
            run_id=run.id,
            urn="920001",
            status="submitted_batch",
            attempt_count=1,
            failure_reason_codes=(),
            completed_at=None,
            data_version_hash="hash-1",
            provider_name="grok",
            provider_batch_id="batch-1",
            prompt_version="overview.v1",
            submitted_at=datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc),
        )
    )

    items = repository.list_pending_batch_run_items("overview", run.id)

    assert len(items) == 1
    assert items[0].provider_batch_id == "batch-1"
    assert items[0].status == "submitted_batch"


def test_summary_repository_preserves_batch_metadata_on_terminal_update(engine: Engine) -> None:
    repository = PostgresSummaryRepository(engine=engine)
    run = repository.create_run(trigger="manual", requested_count=1, summary_kind="overview")
    repository.upsert_run_item(
        item=SummaryGenerationRunItem(
            run_id=run.id,
            urn="920001",
            status="submitted_batch",
            attempt_count=1,
            failure_reason_codes=(),
            completed_at=None,
            data_version_hash="hash-1",
            provider_name="grok",
            provider_batch_id="batch-1",
            prompt_version="overview.v1",
            submitted_at=datetime(2026, 3, 5, 12, 0, tzinfo=timezone.utc),
        )
    )
    repository.upsert_run_item(
        item=SummaryGenerationRunItem(
            run_id=run.id,
            urn="920001",
            status="validation_failed",
            attempt_count=2,
            failure_reason_codes=("non_context_entity_reference",),
            completed_at=datetime(2026, 3, 5, 12, 15, tzinfo=timezone.utc),
            data_version_hash="hash-1",
        )
    )

    items = repository.list_run_items(run.id)

    assert len(items) == 1
    assert items[0].status == "validation_failed"
    assert items[0].provider_name == "grok"
    assert items[0].provider_batch_id == "batch-1"
    assert items[0].prompt_version == "overview.v1"


def _run_item(
    run_id,
    urn: str,
    status: str,
    reason_codes: tuple[str, ...],
    attempt_count: int,
) -> SummaryGenerationRunItem:
    return SummaryGenerationRunItem(
        run_id=run_id,
        urn=urn,
        status=status,
        attempt_count=attempt_count,
        failure_reason_codes=reason_codes,
        completed_at=datetime(2026, 3, 5, 12, 30, tzinfo=timezone.utc),
    )
