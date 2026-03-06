from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.pipelines.base import PipelineRunContext, PipelineSource
from civitas.infrastructure.pipelines.gias import GiasPipeline


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
    reason="Postgres database unavailable for GIAS integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    engine = _build_engine(DATABASE_URL)
    _ensure_schema(engine)
    try:
        yield engine
    finally:
        _cleanup_schools(engine)
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
                CREATE TABLE IF NOT EXISTS pipeline_normalization_warnings (
                    id bigserial PRIMARY KEY,
                    run_id uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
                    source text NOT NULL,
                    field_name text NOT NULL,
                    reason_code text NOT NULL,
                    warning_count integer NOT NULL,
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
                    website text NULL,
                    telephone text NULL,
                    head_title text NULL,
                    head_first_name text NULL,
                    head_last_name text NULL,
                    head_job_title text NULL,
                    address_street text NULL,
                    address_locality text NULL,
                    address_line3 text NULL,
                    address_town text NULL,
                    address_county text NULL,
                    statutory_low_age integer NULL,
                    statutory_high_age integer NULL,
                    gender text NULL,
                    religious_character text NULL,
                    diocese text NULL,
                    admissions_policy text NULL,
                    sixth_form text NULL,
                    nursery_provision text NULL,
                    boarders text NULL,
                    fsm_pct_gias double precision NULL,
                    trust_name text NULL,
                    trust_flag text NULL,
                    federation_name text NULL,
                    federation_flag text NULL,
                    la_name text NULL,
                    la_code text NULL,
                    urban_rural text NULL,
                    number_of_boys integer NULL,
                    number_of_girls integer NULL,
                    lsoa_code text NULL,
                    lsoa_name text NULL,
                    last_changed_date date NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        for statement in (
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS website text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS telephone text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS head_title text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS head_first_name text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS head_last_name text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS head_job_title text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS address_street text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS address_locality text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS address_line3 text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS address_town text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS address_county text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS statutory_low_age integer NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS statutory_high_age integer NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS gender text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS religious_character text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS diocese text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS admissions_policy text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS sixth_form text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS nursery_provision text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS boarders text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS fsm_pct_gias double precision NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS trust_name text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS trust_flag text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS federation_name text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS federation_flag text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS la_name text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS la_code text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS urban_rural text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS number_of_boys integer NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS number_of_girls integer NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS lsoa_code text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS lsoa_name text NULL",
            "ALTER TABLE schools ADD COLUMN IF NOT EXISTS last_changed_date date NULL",
        ):
            connection.execute(text(statement))
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_schools_location
                ON schools USING GIST (location)
                """
            )
        )


def _cleanup_schools(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM schools
                WHERE urn IN ('100001', '100002', '100004', '100005')
                """
            )
        )
        connection.execute(
            text("DELETE FROM pipeline_normalization_warnings WHERE source = 'gias'")
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
        source=PipelineSource.GIAS,
        started_at=datetime(2026, 2, 27, 12, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _copy_fixture_to_bronze(context: PipelineRunContext) -> None:
    fixture_path = (
        Path(__file__).resolve().parents[1] / "fixtures" / "gias" / "edubasealldata_mixed.csv"
    )
    context.bronze_source_path.mkdir(parents=True, exist_ok=True)
    target = context.bronze_source_path / "edubasealldata.csv"
    target.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")


def test_gias_pipeline_stage_and_promote_are_idempotent(engine: Engine, tmp_path: Path) -> None:
    bronze_root = tmp_path / "bronze"
    pipeline = GiasPipeline(engine=engine)

    first_context = _build_context(bronze_root)
    _copy_fixture_to_bronze(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 2
    assert first_stage.rejected_rows == 3

    first_promoted_rows = pipeline.promote(first_context)
    assert first_promoted_rows == 2

    with engine.connect() as connection:
        total_rows = connection.execute(text("SELECT COUNT(*) FROM schools")).scalar_one()
        assert total_rows >= 2
        staged_rows = connection.execute(
            text("SELECT COUNT(*) FROM schools WHERE urn IN ('100001', '100002')")
        ).scalar_one()
        assert staged_rows == 2
        invalid_geom_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM schools
                WHERE urn IN ('100001', '100002')
                  AND (
                    NOT ST_IsValid(location::geometry)
                    OR ST_Y(location::geometry) NOT BETWEEN 49 AND 61
                    OR ST_X(location::geometry) NOT BETWEEN -8 AND 2
                  )
                """
            )
        ).scalar_one()
        assert invalid_geom_rows == 0
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
            "invalid_coordinate_range",
            "invalid_open_date",
        }
        warning_counts = {
            (row[0], row[1]): row[2]
            for row in connection.execute(
                text(
                    """
                    SELECT field_name, reason_code, warning_count
                    FROM pipeline_normalization_warnings
                    WHERE run_id = :run_id
                    """
                ),
                {"run_id": str(first_context.run_id)},
            )
        }
        assert warning_counts == {
            ("SchoolWebsite", "invalid_website"): 1,
            ("TelephoneNum", "invalid_telephone"): 1,
            ("StatutoryHighAge", "age_out_of_range"): 1,
            ("PercentageFSM", "percentage_out_of_range"): 1,
            ("NumberOfBoys", "invalid_integer"): 1,
            ("LastChangedDate", "invalid_date"): 1,
        }
        enriched_school = (
            connection.execute(
                text(
                    """
                SELECT
                    website,
                    telephone,
                    statutory_low_age,
                    statutory_high_age,
                    fsm_pct_gias,
                    la_name,
                    lsoa_code,
                    last_changed_date
                FROM schools
                WHERE urn = '100001'
                """
                )
            )
            .mappings()
            .one()
        )
        assert enriched_school["website"] == "https://alphaprimary.example"
        assert enriched_school["telephone"] == "+442079460123"
        assert enriched_school["statutory_low_age"] == 4
        assert enriched_school["statutory_high_age"] == 11
        assert enriched_school["fsm_pct_gias"] == pytest.approx(12.4)
        assert enriched_school["la_name"] == "Westminster"
        assert enriched_school["lsoa_code"] == "E01004736"
        assert str(enriched_school["last_changed_date"]) == "2026-01-15"

    second_context = _build_context(bronze_root)
    _insert_run_row(engine, second_context)
    second_stage = pipeline.stage(second_context)
    assert second_stage.staged_rows == 2
    assert second_stage.rejected_rows == 3

    second_promoted_rows = pipeline.promote(second_context)
    assert second_promoted_rows == 2

    with engine.connect() as connection:
        staged_rows_after_second_run = connection.execute(
            text("SELECT COUNT(*) FROM schools WHERE urn IN ('100001', '100002')")
        ).scalar_one()
        assert staged_rows_after_second_run == 2
