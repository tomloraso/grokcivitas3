from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.pipelines.base import PipelineRunContext, PipelineSource
from civitas.infrastructure.pipelines.ons_imd import (
    BRONZE_FILE_NAME,
    BRONZE_METADATA_FILE_NAME,
    IMD_RELEASE_IOD2025,
    OnsImdPipeline,
)


def _database_url() -> str:
    return AppSettings().database.url


def _build_engine(database_url: str) -> Engine:
    if database_url.startswith("postgresql"):
        return create_engine(database_url, future=True, connect_args={"connect_timeout": 2})
    return create_engine(database_url, future=True)


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
    reason="Postgres database unavailable for ONS IMD integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    engine = _build_engine(DATABASE_URL)
    _ensure_schema(engine)
    try:
        yield engine
    finally:
        _cleanup(engine)
        engine.dispose()


def _ensure_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id uuid PRIMARY KEY,
                    source text NOT NULL,
                    status text NOT NULL,
                    started_at timestamptz NOT NULL,
                    finished_at timestamptz NULL,
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
                CREATE TABLE IF NOT EXISTS pipeline_rejections (
                    id bigserial PRIMARY KEY,
                    run_id uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
                    source text NOT NULL,
                    stage text NOT NULL,
                    reason_code text NOT NULL,
                    raw_record jsonb NULL,
                    created_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS area_deprivation (
                    lsoa_code text PRIMARY KEY,
                    lsoa_name text NOT NULL,
                    local_authority_district_code text NULL,
                    local_authority_district_name text NULL,
                    imd_score double precision NOT NULL,
                    imd_rank integer NOT NULL,
                    imd_decile integer NOT NULL,
                    idaci_score double precision NOT NULL,
                    idaci_rank integer NOT NULL,
                    idaci_decile integer NOT NULL,
                    source_release text NOT NULL,
                    lsoa_vintage text NOT NULL,
                    source_file_url text NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM area_deprivation
                WHERE lsoa_code IN ('E01000001', 'E01000002')
                """
            )
        )


def _insert_run_row(engine: Engine, context: PipelineRunContext) -> None:
    with engine.begin() as connection:
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
                    'running',
                    :started_at,
                    :bronze_path,
                    0,
                    0,
                    0,
                    0
                )
                ON CONFLICT (run_id) DO NOTHING
                """
            ),
            {
                "run_id": str(context.run_id),
                "source": context.source.value,
                "started_at": context.started_at,
                "bronze_path": str(context.bronze_source_path),
            },
        )


def _build_context(bronze_root: Path) -> PipelineRunContext:
    return PipelineRunContext(
        run_id=uuid4(),
        source=PipelineSource.ONS_IMD,
        started_at=datetime(2026, 3, 2, 21, 15, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _copy_fixture_to_bronze(context: PipelineRunContext) -> None:
    fixture_path = (
        Path(__file__).resolve().parents[1] / "fixtures" / "ons_imd" / "file_7_mixed_2025.csv"
    )
    context.bronze_source_path.mkdir(parents=True, exist_ok=True)
    target = context.bronze_source_path / BRONZE_FILE_NAME
    target.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")

    metadata_payload = {
        "source_file_url": "https://example.com/file_7_mixed_2025.csv",
        "source_release": IMD_RELEASE_IOD2025,
        "source_release_label": "IoD2025",
        "lsoa_vintage": "2021",
    }
    (context.bronze_source_path / BRONZE_METADATA_FILE_NAME).write_text(
        json.dumps(metadata_payload), encoding="utf-8"
    )


def test_ons_imd_pipeline_stage_and_promote_are_idempotent(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    pipeline = OnsImdPipeline(engine=engine, source_release=IMD_RELEASE_IOD2025)

    first_context = _build_context(bronze_root)
    _copy_fixture_to_bronze(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 2
    assert first_stage.rejected_rows == 4

    first_promoted_rows = pipeline.promote(first_context)
    assert first_promoted_rows == 2

    with engine.connect() as connection:
        promoted_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM area_deprivation
                WHERE lsoa_code IN ('E01000001', 'E01000002')
                """
            )
        ).scalar_one()
        assert promoted_rows == 2

        deduped_row = connection.execute(
            text(
                """
                SELECT
                    imd_score,
                    imd_rank,
                    idaci_score,
                    source_release,
                    lsoa_vintage
                FROM area_deprivation
                WHERE lsoa_code = 'E01000001'
                """
            )
        ).one()
        assert deduped_row == (24.0, 95, 0.4, "IoD2025", "2021")

        rejection_reason_codes = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT reason_code
                    FROM pipeline_rejections
                    WHERE run_id = :run_id
                    """
                ),
                {"run_id": str(first_context.run_id)},
            )
        }
        assert rejection_reason_codes == {
            "missing_lsoa_code",
            "missing_lsoa_name",
            "invalid_imd_decile",
            "invalid_idaci_score",
        }

    second_context = _build_context(bronze_root)
    _insert_run_row(engine, second_context)
    second_stage = pipeline.stage(second_context)
    assert second_stage.staged_rows == 2
    assert second_stage.rejected_rows == 4

    second_promoted_rows = pipeline.promote(second_context)
    assert second_promoted_rows == 2

    with engine.connect() as connection:
        total_rows_after_second_run = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM area_deprivation
                WHERE lsoa_code IN ('E01000001', 'E01000002')
                """
            )
        ).scalar_one()
        assert total_rows_after_second_run == 2
