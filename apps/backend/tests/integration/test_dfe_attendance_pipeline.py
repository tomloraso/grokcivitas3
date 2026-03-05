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
from civitas.infrastructure.pipelines.dfe_attendance import (
    BRONZE_MANIFEST_FILE_NAME,
    DfeAttendancePipeline,
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
    reason="Postgres database unavailable for DfE attendance pipeline integration test.",
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
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
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
                CREATE TABLE IF NOT EXISTS schools (
                    urn text PRIMARY KEY,
                    name text NOT NULL,
                    phase text NULL,
                    type text NULL,
                    status text NULL,
                    postcode text NULL,
                    easting double precision NOT NULL,
                    northing double precision NOT NULL,
                    location geography(Point, 4326) NOT NULL,
                    capacity integer NULL,
                    pupil_count integer NULL,
                    open_date date NULL,
                    close_date date NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_attendance_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    overall_attendance_pct double precision NULL,
                    overall_absence_pct double precision NULL,
                    persistent_absence_pct double precision NULL,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year)
                )
                """
            )
        )


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM school_attendance_yearly WHERE urn IN ('100001', '100002')")
        )
        connection.execute(text("DELETE FROM schools WHERE urn IN ('100001', '100002')"))


def _seed_schools(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn, name, phase, type, status, postcode,
                    easting, northing, location, updated_at
                ) VALUES
                (
                    '100001', 'Alpha School', 'Primary', 'Community school', 'Open', 'SW1A 1AA',
                    529090, 179645,
                    ST_GeogFromText('SRID=4326;POINT(-0.141 51.501)'),
                    timezone('utc', now())
                ),
                (
                    '100002', 'Beta School', 'Primary', 'Community school', 'Open', 'SW1A 2AA',
                    529200, 179700,
                    ST_GeogFromText('SRID=4326;POINT(-0.140 51.502)'),
                    timezone('utc', now())
                )
                ON CONFLICT (urn) DO NOTHING
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


def _context(bronze_root: Path) -> PipelineRunContext:
    return PipelineRunContext(
        run_id=uuid4(),
        source=PipelineSource.DFE_ATTENDANCE,
        started_at=datetime(2026, 3, 5, 15, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _write_manifest_and_csv(context: PipelineRunContext) -> None:
    context.bronze_source_path.mkdir(parents=True, exist_ok=True)
    csv_name = "dfe_attendance_2023_24_file-2024.csv"
    (context.bronze_source_path / csv_name).write_text(
        "school_urn,time_period,geographic_level,time_identifier,sess_overall_percent,enrolments_pa_10_exact_percent\n"
        "100001,202223,School,Academic year,6.5,15.0\n"
        "100001,202324,School,Academic year,6.1,14.2\n"
        "100002,202324,School,Academic year,SUPP,.\n"
        ",202324,School,Academic year,5.0,10.0\n"
        "100001,202324,National,Academic year,6.1,14.2\n",
        encoding="utf-8",
    )
    manifest_payload = {
        "normalization_contract_version": "dfe_attendance.v1",
        "lookback_years": 2,
        "assets": [
            {
                "publication_slug": "pupil-absence-in-schools-in-england",
                "release_slug": "2023-24",
                "release_version_id": "attendance-rv-2024",
                "file_id": "file-2024",
                "file_name": "School level absence data",
                "bronze_file_name": csv_name,
                "downloaded_at": "2026-03-05T15:00:00+00:00",
                "sha256": "sha-attendance",
                "row_count": 5,
            }
        ],
    }
    (context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME).write_text(
        json.dumps(manifest_payload),
        encoding="utf-8",
    )


def test_dfe_attendance_pipeline_stage_and_promote_are_idempotent(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    _seed_schools(engine)

    pipeline = DfeAttendancePipeline(
        engine=engine,
        publication_slug="pupil-absence-in-schools-in-england",
        release_slugs=("2022-23", "2023-24"),
        lookback_years=2,
    )

    first_context = _context(bronze_root)
    _write_manifest_and_csv(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 3
    assert first_stage.rejected_rows == 1

    first_promoted = pipeline.promote(first_context)
    assert first_promoted == 3

    with engine.connect() as connection:
        total_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_attendance_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert total_rows == 3

        row_202324 = connection.execute(
            text(
                """
                SELECT
                    overall_attendance_pct,
                    overall_absence_pct,
                    persistent_absence_pct,
                    source_dataset_id,
                    source_dataset_version
                FROM school_attendance_yearly
                WHERE urn = '100001' AND academic_year = '2023/24'
                """
            )
        ).one()
        assert row_202324[0] == pytest.approx(93.9)
        assert row_202324[1] == 6.1
        assert row_202324[2] == 14.2
        assert row_202324[3] == "attendance:attendance-rv-2024"
        assert row_202324[4] == "attendance:file-2024"

        row_suppressed = connection.execute(
            text(
                """
                SELECT overall_attendance_pct, overall_absence_pct, persistent_absence_pct
                FROM school_attendance_yearly
                WHERE urn = '100002' AND academic_year = '2023/24'
                """
            )
        ).one()
        assert row_suppressed[0] is None
        assert row_suppressed[1] is None
        assert row_suppressed[2] is None

    second_context = _context(bronze_root)
    _insert_run_row(engine, second_context)
    second_stage = pipeline.stage(second_context)
    second_promoted = pipeline.promote(second_context)

    assert second_stage.staged_rows == 3
    assert second_promoted == 3

    with engine.connect() as connection:
        total_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_attendance_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert total_rows == 3
