from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.pipelines.base import PipelineRunContext, PipelineSource
from civitas.infrastructure.pipelines.ks4_subject_performance import (
    Ks4SubjectPerformancePipeline,
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
    reason="Postgres database unavailable for KS4 subject performance pipeline integration test.",
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
                    easting double precision NULL,
                    northing double precision NULL,
                    location geography(Point, 4326) NULL
                )
                """
            )
        )
        connection.execute(
            text("ALTER TABLE schools ADD COLUMN IF NOT EXISTS easting double precision NULL")
        )
        connection.execute(
            text("ALTER TABLE schools ADD COLUMN IF NOT EXISTS northing double precision NULL")
        )
        connection.execute(
            text(
                "ALTER TABLE schools ADD COLUMN IF NOT EXISTS location geography(Point, 4326) NULL"
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_ks4_subject_results_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    school_laestab text NULL,
                    school_name text NOT NULL,
                    old_la_code text NULL,
                    new_la_code text NULL,
                    la_name text NULL,
                    source_version text NOT NULL,
                    source_downloaded_at_utc timestamptz NOT NULL,
                    establishment_type_group text NULL,
                    pupil_count integer NULL,
                    qualification_type text NOT NULL,
                    qualification_family text NOT NULL,
                    qualification_detailed text NULL,
                    grade_structure text NOT NULL,
                    subject text NOT NULL,
                    discount_code text NULL,
                    subject_discount_group text NULL,
                    grade text NOT NULL,
                    number_achieving integer NULL,
                    source_file_url text NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (
                        urn,
                        academic_year,
                        qualification_type,
                        subject,
                        grade,
                        source_version
                    )
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_subject_summary_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    key_stage text NOT NULL,
                    qualification_family text NOT NULL,
                    exam_cohort text NOT NULL DEFAULT '',
                    subject text NOT NULL,
                    source_version text NOT NULL,
                    entries_count_total integer NOT NULL,
                    high_grade_count integer NULL,
                    high_grade_share_pct numeric(7,4) NULL,
                    pass_grade_count integer NULL,
                    pass_grade_share_pct numeric(7,4) NULL,
                    ranking_eligible boolean NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (
                        urn,
                        academic_year,
                        key_stage,
                        qualification_family,
                        exam_cohort,
                        subject
                    )
                )
                """
            )
        )


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM school_subject_summary_yearly WHERE urn IN ('100001', '100002')")
        )
        connection.execute(
            text("DELETE FROM school_ks4_subject_results_yearly WHERE urn IN ('100001', '100002')")
        )
        connection.execute(text("DELETE FROM schools WHERE urn IN ('100001', '100002')"))
        connection.execute(
            text("DELETE FROM pipeline_rejections WHERE source = 'ks4_subject_performance'")
        )


def _seed_schools(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (urn, name, easting, northing, location) VALUES
                (
                    '100001',
                    'Alpha School',
                    529090,
                    179645,
                    ST_GeogFromText('SRID=4326;POINT(-0.141 51.501)')
                ),
                (
                    '100002',
                    'Beta School',
                    531120,
                    181500,
                    ST_GeogFromText('SRID=4326;POINT(-0.102 51.521)')
                )
                ON CONFLICT (urn) DO UPDATE SET
                    name = EXCLUDED.name,
                    easting = EXCLUDED.easting,
                    northing = EXCLUDED.northing,
                    location = EXCLUDED.location
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
        source=PipelineSource.KS4_SUBJECT_PERFORMANCE,
        started_at=datetime(2026, 3, 11, 16, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _write_source_file(source_root: Path) -> Path:
    source_root.mkdir(parents=True, exist_ok=True)
    csv_path = source_root / "ks4_subject_performance.csv"
    csv_path.write_text(
        "time_period,time_identifier,geographic_level,country_code,country_name,"
        "school_laestab,school_urn,school_name,old_la_code,new_la_code,la_name,version,"
        "establishment_type_group,pupil_count,qualification_type,qualification_detailed,"
        "grade_structure,subject,discount_code,subject_discount_group,grade,number_achieving\n"
        "202425,Academic year,School,E92000001,England,2136007,100001,Alpha School,213,"
        "E09000033,Westminster,Revised,Local authority maintained schools,118,GCSE,"
        "GCSE (9-1) Full Course,9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X,"
        "Art and Design,JA2,Art & Design,7,2\n"
        "202425,Academic year,School,E92000001,England,2136007,100001,Alpha School,213,"
        "E09000033,Westminster,Revised,Local authority maintained schools,118,GCSE,"
        "GCSE (9-1) Full Course,9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X,"
        "Art and Design,KJ1,Photography,7,1\n"
        "202425,Academic year,School,E92000001,England,2136007,100001,Alpha School,213,"
        "E09000033,Westminster,Revised,Local authority maintained schools,118,GCSE,"
        "GCSE (9-1) Full Course,9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X,"
        "Art and Design,JA2,Art & Design,4,3\n"
        "202425,Academic year,School,E92000001,England,9999999,999999,Missing School,213,"
        "E09000033,Westminster,Revised,Local authority maintained schools,118,GCSE,"
        "GCSE (9-1) Full Course,9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X,"
        "Art and Design,JA2,Art & Design,5,1\n",
        encoding="utf-8",
    )
    return csv_path


def test_ks4_subject_performance_pipeline_promotes_subject_level_rows(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    source_root = tmp_path / "source"
    source_csv = _write_source_file(source_root)
    _seed_schools(engine)
    pipeline = Ks4SubjectPerformancePipeline(
        engine=engine,
        source_csv=str(source_csv),
        source_url="https://example.com/ks4.csv",
        release_page_url="https://example.com/ks4-release",
        data_catalogue_url="https://example.com/ks4-catalogue",
    )

    context = _context(bronze_root)
    _insert_run_row(engine, context)

    assert pipeline.download(context) == 4
    stage_result = pipeline.stage(context)
    assert stage_result.staged_rows == 4
    assert stage_result.rejected_rows == 0

    promoted_rows = pipeline.promote(context)
    assert promoted_rows == 2

    with engine.connect() as connection:
        detail_rows = tuple(
            connection.execute(
                text(
                    """
                    SELECT subject, grade, number_achieving, discount_code, subject_discount_group
                    FROM school_ks4_subject_results_yearly
                    WHERE urn = '100001'
                    ORDER BY grade DESC
                    """
                )
            ).mappings()
        )
        assert len(detail_rows) == 2
        assert detail_rows[0]["grade"] == "7"
        assert detail_rows[0]["number_achieving"] == 3
        assert detail_rows[0]["discount_code"] is None
        assert detail_rows[1]["grade"] == "4"
        assert detail_rows[1]["number_achieving"] == 3

        summary_row = (
            connection.execute(
                text(
                    """
                    SELECT
                        source_version,
                        entries_count_total,
                        high_grade_count,
                        high_grade_share_pct,
                        pass_grade_count,
                        pass_grade_share_pct,
                        ranking_eligible
                    FROM school_subject_summary_yearly
                    WHERE urn = '100001'
                      AND academic_year = '2024/25'
                      AND key_stage = 'ks4'
                      AND qualification_family = 'gcse'
                      AND exam_cohort = ''
                      AND subject = 'Art and Design'
                    """
                )
            )
            .mappings()
            .one()
        )
        assert summary_row["source_version"] == "revised"
        assert summary_row["entries_count_total"] == 6
        assert summary_row["high_grade_count"] == 3
        assert float(summary_row["high_grade_share_pct"]) == pytest.approx(50.0)
        assert summary_row["pass_grade_count"] == 6
        assert float(summary_row["pass_grade_share_pct"]) == pytest.approx(100.0)
        assert summary_row["ranking_eligible"] is True

        rejection_codes = {
            (row["stage"], row["reason_code"])
            for row in connection.execute(
                text(
                    """
                    SELECT stage, reason_code
                    FROM pipeline_rejections
                    WHERE source = 'ks4_subject_performance'
                      AND run_id = :run_id
                    """
                ),
                {"run_id": str(context.run_id)},
            ).mappings()
        }
        assert rejection_codes == {("promote", "school_not_found")}
