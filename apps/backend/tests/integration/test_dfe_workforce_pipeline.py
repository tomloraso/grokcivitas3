from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.pipelines.base import PipelineRunContext, PipelineSource
from civitas.infrastructure.pipelines.dfe_workforce import (
    BRONZE_MANIFEST_FILE_NAME,
    DfeWorkforcePipeline,
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
    reason="Postgres database unavailable for DfE workforce pipeline integration test.",
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
                CREATE TABLE IF NOT EXISTS school_workforce_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    pupil_teacher_ratio double precision NULL,
                    supply_staff_pct double precision NULL,
                    teachers_3plus_years_pct double precision NULL,
                    teacher_turnover_pct double precision NULL,
                    qts_pct double precision NULL,
                    qualifications_level6_plus_pct double precision NULL,
                    teacher_headcount_total double precision NULL,
                    teacher_fte_total double precision NULL,
                    headteacher_headcount double precision NULL,
                    deputy_headteacher_headcount double precision NULL,
                    assistant_headteacher_headcount double precision NULL,
                    classroom_teacher_headcount double precision NULL,
                    leadership_headcount double precision NULL,
                    leadership_share_of_teachers double precision NULL,
                    teacher_female_pct double precision NULL,
                    teacher_male_pct double precision NULL,
                    teacher_qts_pct double precision NULL,
                    teacher_unqualified_pct double precision NULL,
                    support_staff_headcount_total double precision NULL,
                    support_staff_fte_total double precision NULL,
                    teaching_assistant_headcount double precision NULL,
                    teaching_assistant_fte double precision NULL,
                    administrative_staff_headcount double precision NULL,
                    auxiliary_staff_headcount double precision NULL,
                    school_business_professional_headcount double precision NULL,
                    leadership_non_teacher_headcount double precision NULL,
                    teacher_average_mean_salary_gbp double precision NULL,
                    teacher_average_median_salary_gbp double precision NULL,
                    teachers_on_leadership_pay_range_pct double precision NULL,
                    teacher_absence_pct double precision NULL,
                    teacher_absence_days_total double precision NULL,
                    teacher_absence_days_average double precision NULL,
                    teacher_absence_days_average_all_teachers double precision NULL,
                    teacher_vacancy_count double precision NULL,
                    teacher_vacancy_rate double precision NULL,
                    teacher_tempfilled_vacancy_count double precision NULL,
                    teacher_tempfilled_vacancy_rate double precision NULL,
                    third_party_support_staff_headcount double precision NULL,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year)
                )
                """
            )
        )
        for column_name in (
            "teacher_headcount_total",
            "teacher_fte_total",
            "headteacher_headcount",
            "deputy_headteacher_headcount",
            "assistant_headteacher_headcount",
            "classroom_teacher_headcount",
            "leadership_headcount",
            "leadership_share_of_teachers",
            "teacher_female_pct",
            "teacher_male_pct",
            "teacher_qts_pct",
            "teacher_unqualified_pct",
            "support_staff_headcount_total",
            "support_staff_fte_total",
            "teaching_assistant_headcount",
            "teaching_assistant_fte",
            "administrative_staff_headcount",
            "auxiliary_staff_headcount",
            "school_business_professional_headcount",
            "leadership_non_teacher_headcount",
            "teacher_average_mean_salary_gbp",
            "teacher_average_median_salary_gbp",
            "teachers_on_leadership_pay_range_pct",
            "teacher_absence_pct",
            "teacher_absence_days_total",
            "teacher_absence_days_average",
            "teacher_absence_days_average_all_teachers",
            "teacher_vacancy_count",
            "teacher_vacancy_rate",
            "teacher_tempfilled_vacancy_count",
            "teacher_tempfilled_vacancy_rate",
            "third_party_support_staff_headcount",
        ):
            connection.execute(
                text(
                    f"""
                    ALTER TABLE school_workforce_yearly
                    ADD COLUMN IF NOT EXISTS {column_name} double precision NULL
                    """
                )
            )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_teacher_characteristics_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    characteristic_group text NOT NULL,
                    characteristic text NOT NULL,
                    grade text NULL,
                    sex text NULL,
                    age_group text NULL,
                    working_pattern text NULL,
                    qts_status text NULL,
                    on_route text NULL,
                    ethnicity_major text NULL,
                    teacher_fte double precision NULL,
                    teacher_headcount double precision NULL,
                    teacher_fte_pct double precision NULL,
                    teacher_headcount_pct double precision NULL,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year, characteristic_group, characteristic)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_support_staff_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    post text NOT NULL,
                    sex text NOT NULL,
                    ethnicity_major text NOT NULL,
                    support_staff_fte double precision NULL,
                    support_staff_headcount double precision NULL,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year, post, sex, ethnicity_major)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_leadership_snapshot (
                    urn text PRIMARY KEY REFERENCES schools(urn) ON DELETE CASCADE,
                    headteacher_name text NULL,
                    headteacher_start_date date NULL,
                    headteacher_tenure_years double precision NULL,
                    leadership_turnover_score double precision NULL,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM school_support_staff_yearly WHERE urn IN ('100001', '100002')")
        )
        connection.execute(
            text(
                "DELETE FROM school_teacher_characteristics_yearly WHERE urn IN ('100001', '100002')"
            )
        )
        connection.execute(
            text("DELETE FROM school_leadership_snapshot WHERE urn IN ('100001', '100002')")
        )
        connection.execute(
            text("DELETE FROM school_workforce_yearly WHERE urn IN ('100001', '100002')")
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
        source=PipelineSource.DFE_WORKFORCE,
        started_at=datetime(2026, 3, 10, 19, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _write_zip(path: Path, entries: dict[str, str]) -> None:
    with ZipFile(path, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)


def _write_manifest_and_assets(context: PipelineRunContext) -> None:
    context.bronze_source_path.mkdir(parents=True, exist_ok=True)

    legacy_name = "dfe_workforce_legacy_2024.csv"
    _write_csv(
        context.bronze_source_path / legacy_name,
        "school_urn,time_period,geographic_level,time_identifier,pupil_teacher_ratio,supply_teacher_pct,teachers_3plus_years_pct,teacher_turnover_pct,qts_pct,qualifications_level6_plus_pct,headteacher_name,headteacher_start_date,headteacher_tenure_years,leadership_turnover_score\n"
        "100001,202324,School,Academic year,16.7,2.8,74.0,10.2,95.1,80.3,A. Smith,2019-09-01,5.5,1.5\n"
        "100001,202425,School,Academic year,16.3,2.4,76.5,9.8,95.2,81.1,A. Jones,2020-09-01,4.5,1.2\n"
        "100002,202425,School,Academic year,SUPP,.,x,na,n/a,ne,,.,SUPP,SUPP\n"
        ",202425,School,Academic year,16.0,2.0,70.0,9.0,95.0,80.0,H. Name,2021-09-01,3.0,1.0\n"
        "ABC,202425,School,Academic year,16.0,2.0,70.0,9.0,95.0,80.0,H. Name,2021-09-01,3.0,1.0\n"
        "12345,202425,School,Academic year,16.0,2.0,70.0,9.0,95.0,80.0,H. Name,2021-09-01,3.0,1.0\n"
        "100001,202425,National,Academic year,16.3,2.4,76.5,9.8,95.2,81.1,A. Jones,2020-09-01,4.5,1.2\n",
    )

    teacher_characteristics_name = "teacher_characteristics_2024.zip"
    _write_zip(
        context.bronze_source_path / teacher_characteristics_name,
        {
            "workforce_teacher_characteristics_school_202425.csv": (
                "time_period,time_identifier,geographic_level,school_urn,school_laestab,school_name,school_type,characteristic_group,characteristic,grade,sex,age_group,working_pattern,qts_status,on_route,ethnicity_major,full_time_equivalent,headcount,fte_school_percent,headcount_school_percent\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Total,Total,Total,Total,Total,Total,Total,Total,Total,46,50,100,100\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Grade,Head teacher,Head teacher,Total,Total,Total,Total,Total,Total,1,1,2.2,2.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Grade,Deputy head teacher,Deputy head teacher,Total,Total,Total,Total,Total,Total,1,1,2.2,2.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Grade,Assistant head teacher,Assistant head teacher,Total,Total,Total,Total,Total,Total,2,2,4.3,4.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Grade,Classroom teacher,Classroom teacher,,,,,,,42,46,91.3,92.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Sex,Female,,Female,,,,,,33,36,71.7,72.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Sex,Male,,Male,,,,,,13,14,28.3,28.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,QTS status,Qualified,Total,Total,Total,Total,Qualified,Total,Total,44,48,95.7,96.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,QTS status,Unqualified,Total,Total,Total,Total,Unqualified,Total,Total,2,2,4.3,4.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Age group,Under 30,,,Under 30,,,,8,9,17.4,18.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Age group,30 to 39,,,30 to 39,,,,16,17,34.8,34.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Ethnicity Major,White,,,,,,,30,33,65.2,66.0\n"
                "202425,Academic year,School,100001,123/4567,Alpha School,Community school,Ethnicity Major,Asian,,,,,,,8,9,17.4,18.0\n"
            )
        },
    )

    support_staff_name = "support_staff_2024.zip"
    _write_zip(
        context.bronze_source_path / support_staff_name,
        {
            "workforce_support_staff_characteristics_school_202425.csv": (
                "time_period,time_identifier,geographic_level,school_urn,school_laestab,school_name,school_type,post,sex,ethnicity_major,full_time_equivalent,headcount\n"
                "202425,November,School,100001,123/4567,Alpha School,Community school,Teaching assistants,Female,White,8,10\n"
                "202425,November,School,100001,123/4567,Alpha School,Community school,Teaching assistants,Male,White,1,1\n"
                "202425,November,School,100001,123/4567,Alpha School,Community school,Administrative staff,Female,White,4,5\n"
                "202425,November,School,100001,123/4567,Alpha School,Community school,Auxiliary staff,Female,White,2,3\n"
                "202425,November,School,100001,123/4567,Alpha School,Community school,School business professionals,Female,White,1,1\n"
                "202425,November,School,100001,123/4567,Alpha School,Community school,Leadership - Non Teacher,Female,White,1,1\n"
                "202425,November,School,100001,123/4567,Alpha School,Community school,Other school support staff,Male,White,3,4\n"
            )
        },
    )

    teacher_pay_name = "teacher_pay_2024.csv"
    _write_csv(
        context.bronze_source_path / teacher_pay_name,
        "time_period,time_identifier,geographic_level,school_urn,school_name,headcount_all,average_mean,average_median,teachers_on_leadership_pay_range_percent\n"
        "202425,Academic year,School,100001,Alpha School,50,43562.7,42984.0,8.0\n",
    )

    teacher_absence_name = "teacher_absence_2024.csv"
    _write_csv(
        context.bronze_source_path / teacher_absence_name,
        "time_period,time_identifier,geographic_level,school_urn,school_name,total_teachers_taking_absence,percentage_taking_absence,total_number_of_days_lost,average_number_of_days_taken,average_number_of_days_all_teachers\n"
        "202425,Academic year,School,100001,Alpha School,18,36.0,124,6.9,2.5\n",
    )

    teacher_vacancies_name = "teacher_vacancies_2024.csv"
    _write_csv(
        context.bronze_source_path / teacher_vacancies_name,
        "time_period,time_identifier,geographic_level,school_urn,school_name,vacancy,rate,tempfilled,temprate\n"
        "202425,Academic year,School,100001,Alpha School,2,4.0,1,2.0\n",
    )

    third_party_name = "third_party_support_2024.csv"
    _write_csv(
        context.bronze_source_path / third_party_name,
        "time_period,time_identifier,geographic_level,school_urn,school_name,post,headcount\n"
        "202425,Academic year,School,100001,Alpha School,Total,3\n"
        "202425,Academic year,School,100001,Alpha School,Teaching assistants,2\n",
    )

    turnover_empty_name = "teacher_turnover_empty_2024.csv"
    _write_csv(context.bronze_source_path / turnover_empty_name, "")

    manifest_payload = {
        "normalization_contract_version": "dfe_workforce.v2",
        "lookback_years": 2,
        "assets": [
            {
                "asset_kind": "legacy_workforce",
                "file_format": "csv",
                "publication_slug": "school-workforce-in-england",
                "release_slug": "2024",
                "release_version_id": "wf-rv-2025",
                "file_id": "legacy-workforce",
                "file_name": "School workforce legacy metrics",
                "bronze_file_name": legacy_name,
                "downloaded_at": "2026-03-10T19:00:00+00:00",
                "sha256": "sha-legacy",
                "row_count": 7,
            },
            {
                "asset_kind": "teacher_characteristics",
                "file_format": "zip",
                "publication_slug": "school-workforce-in-england",
                "release_slug": "2024",
                "release_version_id": "wf-rv-2025",
                "file_id": "teacher-characteristics",
                "file_name": "Teacher characteristics ZIP",
                "bronze_file_name": teacher_characteristics_name,
                "downloaded_at": "2026-03-10T19:00:00+00:00",
                "sha256": "sha-teacher-characteristics",
                "row_count": 13,
                "zip_entries": ["workforce_teacher_characteristics_school_202425.csv"],
            },
            {
                "asset_kind": "support_staff_characteristics",
                "file_format": "zip",
                "publication_slug": "school-workforce-in-england",
                "release_slug": "2024",
                "release_version_id": "wf-rv-2025",
                "file_id": "support-staff",
                "file_name": "Support staff characteristics ZIP",
                "bronze_file_name": support_staff_name,
                "downloaded_at": "2026-03-10T19:00:00+00:00",
                "sha256": "sha-support-staff",
                "row_count": 7,
                "zip_entries": ["workforce_support_staff_characteristics_school_202425.csv"],
            },
            {
                "asset_kind": "teacher_pay",
                "file_format": "csv",
                "publication_slug": "school-workforce-in-england",
                "release_slug": "2024",
                "release_version_id": "wf-rv-2025",
                "file_id": "teacher-pay",
                "file_name": "Teacher pay CSV",
                "bronze_file_name": teacher_pay_name,
                "downloaded_at": "2026-03-10T19:00:00+00:00",
                "sha256": "sha-teacher-pay",
                "row_count": 1,
            },
            {
                "asset_kind": "teacher_absence",
                "file_format": "csv",
                "publication_slug": "school-workforce-in-england",
                "release_slug": "2024",
                "release_version_id": "wf-rv-2025",
                "file_id": "teacher-absence",
                "file_name": "Teacher absence CSV",
                "bronze_file_name": teacher_absence_name,
                "downloaded_at": "2026-03-10T19:00:00+00:00",
                "sha256": "sha-teacher-absence",
                "row_count": 1,
            },
            {
                "asset_kind": "teacher_vacancies",
                "file_format": "csv",
                "publication_slug": "school-workforce-in-england",
                "release_slug": "2024",
                "release_version_id": "wf-rv-2025",
                "file_id": "teacher-vacancies",
                "file_name": "Teacher vacancies CSV",
                "bronze_file_name": teacher_vacancies_name,
                "downloaded_at": "2026-03-10T19:00:00+00:00",
                "sha256": "sha-teacher-vacancies",
                "row_count": 1,
            },
            {
                "asset_kind": "third_party_support",
                "file_format": "csv",
                "publication_slug": "school-workforce-in-england",
                "release_slug": "2024",
                "release_version_id": "wf-rv-2025",
                "file_id": "third-party-support",
                "file_name": "Third-party support CSV",
                "bronze_file_name": third_party_name,
                "downloaded_at": "2026-03-10T19:00:00+00:00",
                "sha256": "sha-third-party-support",
                "row_count": 2,
            },
            {
                "asset_kind": "teacher_turnover",
                "file_format": "csv",
                "publication_slug": "school-workforce-in-england",
                "release_slug": "2024",
                "release_version_id": "wf-rv-2025",
                "file_id": "teacher-turnover-empty",
                "file_name": "Teacher turnover school level",
                "bronze_file_name": turnover_empty_name,
                "downloaded_at": "2026-03-10T19:00:00+00:00",
                "sha256": "sha-empty-turnover",
                "row_count": 0,
                "source_status": "empty",
            },
        ],
    }
    (context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME).write_text(
        json.dumps(manifest_payload),
        encoding="utf-8",
    )


def test_dfe_workforce_pipeline_stage_and_promote_materialize_workforce_depth(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    _seed_schools(engine)

    pipeline = DfeWorkforcePipeline(
        engine=engine,
        publication_slug="school-workforce-in-england",
        release_slugs=("2023", "2024"),
        lookback_years=2,
    )

    first_context = _context(bronze_root)
    _write_manifest_and_assets(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 28
    assert first_stage.rejected_rows == 3

    first_promoted = pipeline.promote(first_context)
    assert first_promoted == 25

    with engine.connect() as connection:
        rejection_summary = connection.execute(
            text(
                """
                SELECT reason_code, raw_record
                FROM pipeline_rejections
                WHERE run_id = :run_id
                """
            ),
            {"run_id": str(first_context.run_id)},
        ).one()
        assert rejection_summary[0] == "invalid_urn"
        assert rejection_summary[1]["asset_kind"] == "legacy_workforce"
        assert rejection_summary[1]["rejected_count"] == 3
        assert rejection_summary[1]["sample_count"] == 3
        assert rejection_summary[1]["sample_truncated"] is False

        workforce_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_workforce_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert workforce_rows == 3

        workforce_202425 = connection.execute(
            text(
                """
                SELECT
                    pupil_teacher_ratio,
                    teacher_headcount_total,
                    leadership_headcount,
                    leadership_share_of_teachers,
                    teacher_female_pct,
                    teacher_qts_pct,
                    support_staff_headcount_total,
                    teaching_assistant_headcount,
                    teacher_average_mean_salary_gbp,
                    teacher_absence_pct,
                    teacher_vacancy_rate,
                    third_party_support_staff_headcount
                FROM school_workforce_yearly
                WHERE urn = '100001' AND academic_year = '2024/25'
                """
            )
        ).one()
        assert workforce_202425[0] == pytest.approx(16.3)
        assert workforce_202425[1] == pytest.approx(50.0)
        assert workforce_202425[2] == pytest.approx(4.0)
        assert workforce_202425[3] == pytest.approx(8.0)
        assert workforce_202425[4] == pytest.approx(72.0)
        assert workforce_202425[5] == pytest.approx(96.0)
        assert workforce_202425[6] == pytest.approx(25.0)
        assert workforce_202425[7] == pytest.approx(11.0)
        assert workforce_202425[8] == pytest.approx(43562.7)
        assert workforce_202425[9] == pytest.approx(36.0)
        assert workforce_202425[10] == pytest.approx(4.0)
        assert workforce_202425[11] == pytest.approx(3.0)

        teacher_characteristics_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_teacher_characteristics_yearly
                WHERE urn = '100001' AND academic_year = '2024/25'
                """
            )
        ).scalar_one()
        assert teacher_characteristics_rows == 13

        support_staff_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_support_staff_yearly
                WHERE urn = '100001' AND academic_year = '2024/25'
                """
            )
        ).scalar_one()
        assert support_staff_rows == 7

        leadership = connection.execute(
            text(
                """
                SELECT headteacher_name, headteacher_start_date, headteacher_tenure_years
                FROM school_leadership_snapshot
                WHERE urn = '100001'
                """
            )
        ).one()
        assert leadership[0] == "A. Jones"
        assert str(leadership[1]) == "2020-09-01"
        assert leadership[2] == pytest.approx(4.5)

    second_context = _context(bronze_root)
    _insert_run_row(engine, second_context)
    second_stage = pipeline.stage(second_context)
    second_promoted = pipeline.promote(second_context)

    assert second_stage.staged_rows == 28
    assert second_stage.rejected_rows == 3
    assert second_promoted == 25

    with engine.connect() as connection:
        workforce_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_workforce_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert workforce_rows == 3

        teacher_characteristics_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_teacher_characteristics_yearly
                WHERE urn = '100001' AND academic_year = '2024/25'
                """
            )
        ).scalar_one()
        assert teacher_characteristics_rows == 13

        support_staff_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_support_staff_yearly
                WHERE urn = '100001' AND academic_year = '2024/25'
                """
            )
        ).scalar_one()
        assert support_staff_rows == 7
