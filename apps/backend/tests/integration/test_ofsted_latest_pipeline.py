from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.pipelines.base import PipelineRunContext, PipelineSource
from civitas.infrastructure.pipelines.ofsted_latest import BRONZE_FILE_NAME, OfstedLatestPipeline


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
    reason="Postgres database unavailable for Ofsted latest integration test.",
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
                CREATE TABLE IF NOT EXISTS school_ofsted_latest (
                    urn text PRIMARY KEY REFERENCES schools(urn) ON DELETE CASCADE,
                    inspection_start_date date NULL,
                    publication_date date NULL,
                    overall_effectiveness_code text NULL,
                    overall_effectiveness_label text NULL,
                    provider_page_url text NULL,
                    latest_oeif_inspection_start_date date NULL,
                    latest_oeif_publication_date date NULL,
                    quality_of_education_code text NULL,
                    quality_of_education_label text NULL,
                    behaviour_and_attitudes_code text NULL,
                    behaviour_and_attitudes_label text NULL,
                    personal_development_code text NULL,
                    personal_development_label text NULL,
                    leadership_and_management_code text NULL,
                    leadership_and_management_label text NULL,
                    latest_ungraded_inspection_date date NULL,
                    latest_ungraded_publication_date date NULL,
                    is_graded boolean NOT NULL DEFAULT false,
                    ungraded_outcome text NULL,
                    source_asset_url text NOT NULL,
                    source_asset_month text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS provider_page_url text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS latest_oeif_inspection_start_date date NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS latest_oeif_publication_date date NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS quality_of_education_code text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS quality_of_education_label text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS behaviour_and_attitudes_code text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS behaviour_and_attitudes_label text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS personal_development_code text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS personal_development_label text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS leadership_and_management_code text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS leadership_and_management_label text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS latest_ungraded_inspection_date date NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_ofsted_latest "
                "ADD COLUMN IF NOT EXISTS latest_ungraded_publication_date date NULL"
            )
        )
    _seed_schools(engine)


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
                    ST_GeogFromText('SRID=4326;POINT(-0.141 51.501)'),
                    timezone('utc', now())
                ),
                (
                    '100002', 'Beta Primary', 'Primary', 'Community school', 'Open', 'SW1A 2AA',
                    529200, 179700,
                    ST_GeogFromText('SRID=4326;POINT(-0.140 51.502)'),
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
                DELETE FROM school_ofsted_latest
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
        source=PipelineSource.OFSTED_LATEST,
        started_at=datetime(2026, 3, 2, 16, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _copy_fixture_to_bronze(context: PipelineRunContext) -> None:
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "ofsted_latest"
        / "latest_inspections_mixed.csv"
    )
    context.bronze_source_path.mkdir(parents=True, exist_ok=True)
    target = context.bronze_source_path / BRONZE_FILE_NAME
    target.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")

    metadata_path = target.with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(
            {
                "source_asset_url": (
                    "https://assets.publishing.service.gov.uk/media/abc123/"
                    "Management_information_-_state-funded_schools_-_"
                    "latest_inspections_as_at_31_Jan_2026.csv"
                ),
                "source_asset_month": "2026-01",
            }
        ),
        encoding="utf-8",
    )


def test_ofsted_latest_pipeline_stage_and_promote_are_idempotent(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    pipeline = OfstedLatestPipeline(engine=engine)

    first_context = _build_context(bronze_root)
    _copy_fixture_to_bronze(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 2
    assert first_stage.rejected_rows == 3

    first_promoted_rows = pipeline.promote(first_context)
    assert first_promoted_rows == 2

    with engine.connect() as connection:
        promoted_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_ofsted_latest
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert promoted_rows == 2

        ofsted_100001 = connection.execute(
            text(
                """
                SELECT
                    overall_effectiveness_code,
                    overall_effectiveness_label,
                    provider_page_url,
                    quality_of_education_code,
                    behaviour_and_attitudes_code,
                    is_graded,
                    source_asset_month
                FROM school_ofsted_latest
                WHERE urn = '100001'
                """
            )
        ).one()
        assert ofsted_100001 == (
            "1",
            "Outstanding",
            "https://reports.ofsted.gov.uk/inspection-reports/find-inspection-report/provider/ELS/100001",
            "1",
            "2",
            True,
            "2026-01",
        )

        ofsted_100002 = connection.execute(
            text(
                """
                SELECT
                    overall_effectiveness_code,
                    overall_effectiveness_label,
                    is_graded,
                    latest_ungraded_inspection_date,
                    ungraded_outcome
                FROM school_ofsted_latest
                WHERE urn = '100002'
                """
            )
        ).one()
        assert ofsted_100002 == (None, None, False, date(2025, 12, 5), "Maintained standards")

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
            "missing_urn",
            "invalid_inspection_start_date",
            "invalid_overall_effectiveness_code",
        }

    second_context = _build_context(bronze_root)
    _insert_run_row(engine, second_context)

    second_stage = pipeline.stage(second_context)
    assert second_stage.staged_rows == 2
    assert second_stage.rejected_rows == 3

    second_promoted_rows = pipeline.promote(second_context)
    assert second_promoted_rows == 2

    with engine.connect() as connection:
        total_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_ofsted_latest
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert total_rows == 2
