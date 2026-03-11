from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.pipelines.base import PipelineRunContext, PipelineSource
from civitas.infrastructure.pipelines.leaver_destinations import LeaverDestinationsPipeline


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
    reason="Postgres database unavailable for leaver destinations pipeline integration test.",
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
                    establishment_number text NULL,
                    school_laestab text NULL,
                    name text NOT NULL,
                    phase text NULL,
                    type text NULL,
                    status text NULL,
                    postcode text NULL,
                    easting double precision NOT NULL,
                    northing double precision NOT NULL,
                    location geography(Point, 4326) NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_leaver_destinations_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    destination_stage text NOT NULL,
                    qualification_group text NOT NULL DEFAULT '',
                    qualification_level text NOT NULL DEFAULT '',
                    breakdown_topic text NOT NULL,
                    breakdown text NOT NULL,
                    school_name text NOT NULL,
                    school_laestab text NULL,
                    admission_policy text NULL,
                    entry_gender text NULL,
                    institution_group text NULL,
                    institution_type text NULL,
                    cohort_count integer NULL,
                    overall_count integer NULL,
                    overall_pct numeric(7,4) NULL,
                    education_count integer NULL,
                    education_pct numeric(7,4) NULL,
                    apprenticeship_count integer NULL,
                    apprenticeship_pct numeric(7,4) NULL,
                    employment_count integer NULL,
                    employment_pct numeric(7,4) NULL,
                    not_sustained_count integer NULL,
                    not_sustained_pct numeric(7,4) NULL,
                    activity_unknown_count integer NULL,
                    activity_unknown_pct numeric(7,4) NULL,
                    fe_count integer NULL,
                    fe_pct numeric(7,4) NULL,
                    other_education_count integer NULL,
                    other_education_pct numeric(7,4) NULL,
                    school_sixth_form_count integer NULL,
                    school_sixth_form_pct numeric(7,4) NULL,
                    sixth_form_college_count integer NULL,
                    sixth_form_college_pct numeric(7,4) NULL,
                    higher_education_count integer NULL,
                    higher_education_pct numeric(7,4) NULL,
                    source_file_url text NOT NULL,
                    source_updated_at_utc timestamptz NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (
                        urn,
                        academic_year,
                        destination_stage,
                        qualification_group,
                        qualification_level,
                        breakdown_topic,
                        breakdown
                    )
                )
                """
            )
        )


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM school_leaver_destinations_yearly
                WHERE urn IN ('100001', '100002', '200001', '200002')
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM schools
                WHERE urn IN ('100001', '100002', '200001', '200002')
                """
            )
        )
        connection.execute(
            text("DELETE FROM pipeline_rejections WHERE source = 'leaver_destinations'")
        )


def _seed_schools(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn,
                    establishment_number,
                    school_laestab,
                    name,
                    phase,
                    type,
                    status,
                    postcode,
                    easting,
                    northing,
                    location,
                    updated_at
                ) VALUES
                (
                    '100001', '6007', '2136007', 'Alpha School', 'Secondary',
                    'Community school', 'Open', 'SW1A 1AA', 529090, 179645,
                    ST_GeogFromText('SRID=4326;POINT(-0.141 51.501)'), timezone('utc', now())
                ),
                (
                    '100002', '3614', '2013614', 'Beta Sixth Form', '16 to 18',
                    'Academy converter', 'Open', 'EC1A 1BB', 531120, 181500,
                    ST_GeogFromText('SRID=4326;POINT(-0.102 51.521)'), timezone('utc', now())
                ),
                (
                    '200001', '5001', '5555001', 'Ambiguous One', 'Secondary',
                    'Community school', 'Open', 'E1 1AA', 532000, 182000,
                    ST_GeogFromText('SRID=4326;POINT(-0.080 51.530)'), timezone('utc', now())
                ),
                (
                    '200002', '5002', '5555001', 'Ambiguous Two', 'Secondary',
                    'Community school', 'Open', 'E1 1AB', 532050, 182050,
                    ST_GeogFromText('SRID=4326;POINT(-0.079 51.531)'), timezone('utc', now())
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
        source=PipelineSource.LEAVER_DESTINATIONS,
        started_at=datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _write_source_files(source_root: Path) -> tuple[Path, Path]:
    source_root.mkdir(parents=True, exist_ok=True)
    ks4_csv = source_root / "ees_ks4_inst_202223.csv"
    ks4_csv.write_text(
        "time_period,time_identifier,geographic_level,country_code,country_name,region_code,"
        "region_name,old_la_code,new_la_code,la_name,local_authority_selection_status,"
        "school_laestab,school_urn,school_name,admission_policy,entry_gender,"
        "institution_group,institution_type,breakdown_topic,breakdown,data_type,version,"
        "cohort,overall,education,fe,ssf,sfc,other_edu,appren,all_work,all_notsust,"
        "all_unknown\n"
        "202223,Academic year,School,E92000001,England,E12000007,London,213,E09000033,"
        "Westminster,Selected,2136007,100001,Alpha School,Comprehensive,Mixed,"
        "Local authority maintained schools,Community school,Total,Total,Number of students,"
        "1,118,109,72,21,5,8,4,8,21,4,5\n"
        "202223,Academic year,School,E92000001,England,E12000007,London,213,E09000033,"
        "Westminster,Selected,2136007,100001,Alpha School,Comprehensive,Mixed,"
        "Local authority maintained schools,Community school,Total,Total,Percentage,1,"
        "118,92.4,61.0,18.0,4.2,6.8,3.4,6.8,17.8,3.4,4.2\n"
        "202223,Academic year,School,E92000001,England,E12000007,London,999,E09000998,"
        "Conflict,Selected,9999999,100001,Conflict School,Comprehensive,Mixed,"
        "Local authority maintained schools,Community school,Total,Total,Number of students,"
        "1,40,34,24,8,4,4,0,5,5,1,0\n"
        "202223,Academic year,School,E92000001,England,E12000007,London,213,E09000033,"
        "Westminster,Selected,2136007,ABC123,Invalid URN School,Comprehensive,Mixed,"
        "Local authority maintained schools,Community school,Total,Total,Percentage,1,"
        "118,92.4,61.0,18.0,4.2,6.8,3.4,6.8,17.8,3.4,4.2\n",
        encoding="utf-8",
    )
    study_csv = source_root / "ees_ks5_inst_202223.csv"
    study_csv.write_text(
        "time_period,time_identifier,geographic_level,country_code,country_name,region_code,"
        "region_name,old_la_code,new_la_code,la_name,local_authority_selection_status,"
        "school_laestab,school_urn,school_name,admission_policy,entry_gender,"
        "institution_group,institution_type,cohort_level_group,cohort_level,"
        "breakdown_topic,breakdown,data_type,version,cohort,overall,education,he,fe,"
        "other_edu,appren,all_work,all_notsust,all_unknown\n"
        "202223,Academic year,School,E92000001,England,E12000007,London,201,E09000001,"
        "City of London,Selected,2013614,100002,Beta Sixth Form,Not applicable,Mixed,"
        "Academies,Academy converter,Total,Total,Total,Total,Number of students,1,"
        "90,80,56,31,18,7,10,14,6,10\n"
        "202223,Academic year,School,E92000001,England,E12000007,London,201,E09000001,"
        "City of London,Selected,2013614,100002,Beta Sixth Form,Not applicable,Mixed,"
        "Academies,Academy converter,Total,Total,Total,Total,Percentage,1,"
        "90,88.9,62.2,34.4,20.0,7.8,11.1,15.6,6.7,11.1\n"
        "202223,Academic year,School,E92000001,England,E12000007,London,555,E09000997,"
        "Ambiguous,Selected,5555001,999999,Ambiguous School,Not applicable,Mixed,"
        "Academies,Academy converter,Total,Total,Total,Total,Number of students,1,"
        "70,60,41,20,15,6,8,10,5,5\n",
        encoding="utf-8",
    )
    return ks4_csv, study_csv


def test_leaver_destinations_pipeline_stage_and_promote_are_idempotent(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    source_root = tmp_path / "source"
    ks4_csv, study_csv = _write_source_files(source_root)
    _seed_schools(engine)
    pipeline = LeaverDestinationsPipeline(
        engine=engine,
        ks4_source_csv=str(ks4_csv),
        ks4_source_url="https://example.com/ks4.csv",
        ks4_release_page_url="https://example.com/ks4-release",
        ks4_data_catalogue_url="https://example.com/ks4-catalogue",
        study_16_to_18_source_csv=str(study_csv),
        study_16_to_18_source_url="https://example.com/16-to-18.csv",
        study_16_to_18_release_page_url="https://example.com/16-to-18-release",
        study_16_to_18_data_catalogue_url="https://example.com/16-to-18-catalogue",
    )

    first_context = _context(bronze_root)
    _insert_run_row(engine, first_context)
    assert pipeline.download(first_context) == 7

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 6
    assert first_stage.rejected_rows == 1

    first_promoted = pipeline.promote(first_context)
    assert first_promoted == 2

    with engine.connect() as connection:
        destination_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_leaver_destinations_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert destination_rows == 2

        alpha = (
            connection.execute(
                text(
                    """
                    SELECT
                        qualification_group,
                        qualification_level,
                        overall_count,
                        overall_pct,
                        education_count,
                        school_sixth_form_count,
                        sixth_form_college_pct,
                        higher_education_count
                    FROM school_leaver_destinations_yearly
                    WHERE urn = '100001'
                      AND academic_year = '2022/23'
                      AND destination_stage = 'ks4'
                      AND breakdown_topic = 'Total'
                      AND breakdown = 'Total'
                    """
                )
            )
            .mappings()
            .one()
        )
        assert alpha["qualification_group"] == ""
        assert alpha["qualification_level"] == ""
        assert alpha["overall_count"] == 109
        assert float(alpha["overall_pct"]) == pytest.approx(92.4)
        assert alpha["education_count"] == 72
        assert alpha["school_sixth_form_count"] == 5
        assert float(alpha["sixth_form_college_pct"]) == pytest.approx(6.8)
        assert alpha["higher_education_count"] is None

        beta = (
            connection.execute(
                text(
                    """
                    SELECT
                        qualification_group,
                        qualification_level,
                        overall_count,
                        overall_pct,
                        higher_education_count,
                        higher_education_pct,
                        apprenticeship_count,
                        employment_pct
                    FROM school_leaver_destinations_yearly
                    WHERE urn = '100002'
                      AND academic_year = '2022/23'
                      AND destination_stage = '16_to_18'
                      AND breakdown_topic = 'Total'
                      AND breakdown = 'Total'
                    """
                )
            )
            .mappings()
            .one()
        )
        assert beta["qualification_group"] == "Total"
        assert beta["qualification_level"] == "Total"
        assert beta["overall_count"] == 80
        assert float(beta["overall_pct"]) == pytest.approx(88.9)
        assert beta["higher_education_count"] == 31
        assert float(beta["higher_education_pct"]) == pytest.approx(34.4)
        assert beta["apprenticeship_count"] == 10
        assert float(beta["employment_pct"]) == pytest.approx(15.6)

        rejection_codes = {
            (row["stage"], row["reason_code"])
            for row in connection.execute(
                text(
                    """
                    SELECT stage, reason_code
                    FROM pipeline_rejections
                    WHERE source = 'leaver_destinations' AND run_id = :run_id
                    """
                ),
                {"run_id": str(first_context.run_id)},
            ).mappings()
        }
        assert rejection_codes == {
            ("stage", "invalid_school_urn"),
            ("promote", "ambiguous_school_laestab"),
            ("promote", "join_key_conflict"),
        }

    second_context = _context(bronze_root)
    _insert_run_row(engine, second_context)
    second_stage = pipeline.stage(second_context)
    second_promoted = pipeline.promote(second_context)

    assert second_stage.staged_rows == 6
    assert second_stage.rejected_rows == 1
    assert second_promoted == 2

    with engine.connect() as connection:
        destination_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_leaver_destinations_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert destination_rows == 2
