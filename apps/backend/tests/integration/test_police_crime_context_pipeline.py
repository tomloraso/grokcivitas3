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
from civitas.infrastructure.pipelines.police_crime_context import (
    BRONZE_EXTRACTED_DIR,
    BRONZE_METADATA_FILE_NAME,
    DEFAULT_POLICE_CRIME_RADIUS_METERS,
    PoliceCrimeContextPipeline,
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
    reason="Postgres database unavailable for Police crime context integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    engine = _build_engine(DATABASE_URL)
    _ensure_schema(engine)
    _cleanup(engine)
    _seed_schools(engine)
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
                CREATE TABLE IF NOT EXISTS area_crime_context (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    month date NOT NULL,
                    crime_category text NOT NULL,
                    incident_count integer NOT NULL,
                    radius_meters double precision NOT NULL,
                    source_month text NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, month, crime_category, radius_meters)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS area_crime_global_metadata (
                    id smallint PRIMARY KEY,
                    months_available integer NOT NULL,
                    latest_updated_at timestamptz NULL,
                    latest_month date NULL,
                    latest_radius_meters double precision NULL,
                    refreshed_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )


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
                    '100001', 'Alpha Primary', 'Primary', 'Community school', 'Open', 'SW1A 1AA',
                    529090, 179645,
                    ST_GeogFromText('SRID=4326;POINT(-30.0000 0.0000)'),
                    timezone('utc', now())
                ),
                (
                    '100002', 'Beta Primary', 'Primary', 'Community school', 'Open', 'SW1A 2AA',
                    529200, 179700,
                    ST_GeogFromText('SRID=4326;POINT(-30.0300 0.0000)'),
                    timezone('utc', now())
                )
                ON CONFLICT (urn) DO NOTHING
                """
            )
        )


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM area_crime_context
                WHERE urn IN ('100001', '100002')
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM schools
                WHERE urn IN ('100001', '100002')
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
        source=PipelineSource.POLICE_CRIME_CONTEXT,
        started_at=datetime(2026, 3, 2, 23, 10, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _copy_fixture_to_bronze(context: PipelineRunContext) -> None:
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "police_crime_context"
        / "2026-01-example-street.csv"
    )
    extracted_dir = context.bronze_source_path / BRONZE_EXTRACTED_DIR
    extracted_dir.mkdir(parents=True, exist_ok=True)
    target = extracted_dir / "2026-01-example-street.csv"
    target.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")

    metadata_payload = {
        "source_mode": "archive",
        "source_archive_url": "https://data.police.uk/data/archive/2026-01.zip",
        "source_month": "2026-01",
        "radius_meters": DEFAULT_POLICE_CRIME_RADIUS_METERS,
        "extracted_file_count": 1,
        "rows": 8,
    }
    (context.bronze_source_path / BRONZE_METADATA_FILE_NAME).write_text(
        json.dumps(metadata_payload), encoding="utf-8"
    )


def test_police_crime_context_pipeline_stage_and_promote_are_idempotent(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    pipeline = PoliceCrimeContextPipeline(engine=engine)

    first_context = _build_context(bronze_root)
    _copy_fixture_to_bronze(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 5
    assert first_stage.rejected_rows == 3

    first_promoted_rows = pipeline.promote(first_context)
    assert first_promoted_rows == 3

    with engine.connect() as connection:
        promoted_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM area_crime_context
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert promoted_rows == 3

        global_crime_metadata = connection.execute(
            text(
                """
                SELECT
                    months_available,
                    latest_updated_at,
                    latest_month,
                    latest_radius_meters
                FROM area_crime_global_metadata
                WHERE id = 1
                """
            )
        ).one()
        assert global_crime_metadata[0] >= 1
        assert global_crime_metadata[1] is not None
        assert global_crime_metadata[2] is not None
        assert float(global_crime_metadata[3]) > 0

        alpha_violent = connection.execute(
            text(
                """
                SELECT incident_count, source_month
                FROM area_crime_context
                WHERE urn = '100001'
                  AND month = DATE '2026-01-01'
                  AND crime_category = 'violent-crime'
                  AND radius_meters = :radius_meters
                """
            ),
            {"radius_meters": DEFAULT_POLICE_CRIME_RADIUS_METERS},
        ).one()
        assert alpha_violent == (2, "2026-01")

        beta_robbery = connection.execute(
            text(
                """
                SELECT incident_count
                FROM area_crime_context
                WHERE urn = '100002'
                  AND month = DATE '2026-01-01'
                  AND crime_category = 'robbery'
                  AND radius_meters = :radius_meters
                """
            ),
            {"radius_meters": DEFAULT_POLICE_CRIME_RADIUS_METERS},
        ).scalar_one()
        assert beta_robbery == 1

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
            "missing_longitude",
            "invalid_month",
            "missing_latitude",
        }

    second_context = _build_context(bronze_root)
    _insert_run_row(engine, second_context)
    second_stage = pipeline.stage(second_context)
    assert second_stage.staged_rows == 5
    assert second_stage.rejected_rows == 3

    second_promoted_rows = pipeline.promote(second_context)
    assert second_promoted_rows == 3

    with engine.connect() as connection:
        total_rows_after_second_run = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM area_crime_context
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert total_rows_after_second_run == 3
