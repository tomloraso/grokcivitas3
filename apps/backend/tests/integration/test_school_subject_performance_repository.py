from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_subject_performance_repository import (
    PostgresSubjectPerformanceRepository,
    materialize_school_subject_summaries,
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
    reason="Postgres database unavailable for subject performance repository integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    engine = _build_engine(DATABASE_URL)
    _ensure_schema(engine)
    _cleanup(engine)
    _seed_data(engine)
    try:
        yield engine
    finally:
        _cleanup(engine)
        engine.dispose()


def _ensure_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
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
                CREATE TABLE IF NOT EXISTS school_16_to_18_subject_results_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    school_laestab text NULL,
                    school_name text NOT NULL,
                    old_la_code text NULL,
                    new_la_code text NULL,
                    la_name text NULL,
                    source_version text NOT NULL,
                    source_downloaded_at_utc timestamptz NOT NULL,
                    exam_cohort text NOT NULL,
                    qualification_detailed text NOT NULL,
                    qualification_family text NOT NULL,
                    qualification_level text NULL,
                    a_level_equivalent_size numeric(9,2) NULL,
                    gcse_equivalent_size numeric(9,2) NULL,
                    grade_structure text NOT NULL,
                    subject text NOT NULL,
                    grade text NOT NULL,
                    entries_count integer NULL,
                    source_file_url text NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (
                        urn,
                        academic_year,
                        exam_cohort,
                        qualification_detailed,
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
            text("DELETE FROM school_subject_summary_yearly WHERE urn IN ('930001', '930002')")
        )
        connection.execute(
            text(
                "DELETE FROM school_16_to_18_subject_results_yearly WHERE urn IN ('930001', '930002')"
            )
        )
        connection.execute(
            text("DELETE FROM school_ks4_subject_results_yearly WHERE urn IN ('930001', '930002')")
        )
        connection.execute(text("DELETE FROM schools WHERE urn IN ('930001', '930002')"))


def _seed_data(engine: Engine) -> None:
    revised_downloaded_at = datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc)
    final_downloaded_at = datetime(2026, 3, 11, 12, 0, tzinfo=timezone.utc)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (urn, name, easting, northing, location) VALUES
                (
                    '930001',
                    'Repository Test School',
                    529090,
                    179645,
                    ST_GeogFromText('SRID=4326;POINT(-0.141 51.501)')
                ),
                (
                    '930002',
                    'Empty Subject Performance School',
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
        connection.execute(
            text(
                """
                INSERT INTO school_ks4_subject_results_yearly (
                    urn,
                    academic_year,
                    school_laestab,
                    school_name,
                    old_la_code,
                    new_la_code,
                    la_name,
                    source_version,
                    source_downloaded_at_utc,
                    establishment_type_group,
                    pupil_count,
                    qualification_type,
                    qualification_family,
                    qualification_detailed,
                    grade_structure,
                    subject,
                    discount_code,
                    subject_discount_group,
                    grade,
                    number_achieving,
                    source_file_url
                ) VALUES
                (
                    '930001', '2024/25', '2136007', 'Repository Test School', '213',
                    'E09000033', 'Westminster', 'revised', :revised_downloaded_at,
                    'Local authority maintained schools', 120, 'GCSE', 'gcse',
                    'GCSE (9-1) Full Course', '9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X',
                    'Mathematics', NULL, NULL, '7', 15, 'https://example.com/ks4-revised.csv'
                ),
                (
                    '930001', '2024/25', '2136007', 'Repository Test School', '213',
                    'E09000033', 'Westminster', 'revised', :revised_downloaded_at,
                    'Local authority maintained schools', 120, 'GCSE', 'gcse',
                    'GCSE (9-1) Full Course', '9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X',
                    'Mathematics', NULL, NULL, '4', 10, 'https://example.com/ks4-revised.csv'
                ),
                (
                    '930001', '2024/25', '2136007', 'Repository Test School', '213',
                    'E09000033', 'Westminster', 'final', :final_downloaded_at,
                    'Local authority maintained schools', 120, 'GCSE', 'gcse',
                    'GCSE (9-1) Full Course', '9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X',
                    'Mathematics', NULL, NULL, '7', 18, 'https://example.com/ks4-final.csv'
                ),
                (
                    '930001', '2024/25', '2136007', 'Repository Test School', '213',
                    'E09000033', 'Westminster', 'final', :final_downloaded_at,
                    'Local authority maintained schools', 120, 'GCSE', 'gcse',
                    'GCSE (9-1) Full Course', '9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X',
                    'Mathematics', NULL, NULL, '4', 8, 'https://example.com/ks4-final.csv'
                ),
                (
                    '930001', '2024/25', '2136007', 'Repository Test School', '213',
                    'E09000033', 'Westminster', 'final', :final_downloaded_at,
                    'Local authority maintained schools', 120, 'GCSE', 'gcse',
                    'GCSE (9-1) Full Course', '9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X',
                    'History', NULL, NULL, '7', 4, 'https://example.com/ks4-final.csv'
                ),
                (
                    '930001', '2024/25', '2136007', 'Repository Test School', '213',
                    'E09000033', 'Westminster', 'final', :final_downloaded_at,
                    'Local authority maintained schools', 120, 'GCSE', 'gcse',
                    'GCSE (9-1) Full Course', '9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X',
                    'History', NULL, NULL, '4', 6, 'https://example.com/ks4-final.csv'
                )
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "revised_downloaded_at": revised_downloaded_at,
                "final_downloaded_at": final_downloaded_at,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO school_16_to_18_subject_results_yearly (
                    urn,
                    academic_year,
                    school_laestab,
                    school_name,
                    old_la_code,
                    new_la_code,
                    la_name,
                    source_version,
                    source_downloaded_at_utc,
                    exam_cohort,
                    qualification_detailed,
                    qualification_family,
                    qualification_level,
                    a_level_equivalent_size,
                    gcse_equivalent_size,
                    grade_structure,
                    subject,
                    grade,
                    entries_count,
                    source_file_url
                ) VALUES
                (
                    '930001', '2024/25', '2136007', 'Repository Test School', '213',
                    'E09000033', 'Westminster', 'revised', :revised_downloaded_at,
                    'A level', 'GCE A level', 'a_level', '3', 1.0, 4.0,
                    '*,A,B,C,D,E', 'Physics', 'A*', 6,
                    'https://example.com/16-to-18-revised.csv'
                ),
                (
                    '930001', '2024/25', '2136007', 'Repository Test School', '213',
                    'E09000033', 'Westminster', 'revised', :revised_downloaded_at,
                    'A level', 'GCE A level', 'a_level', '3', 1.0, 4.0,
                    '*,A,B,C,D,E', 'Physics', 'A', 5,
                    'https://example.com/16-to-18-revised.csv'
                )
                ON CONFLICT DO NOTHING
                """
            ),
            {"revised_downloaded_at": revised_downloaded_at},
        )

    with engine.begin() as connection:
        materialize_school_subject_summaries(connection, key_stage="ks4")
        materialize_school_subject_summaries(connection, key_stage="16_to_18")


def test_materializer_prefers_final_version_and_hides_16_to_18_by_default(
    engine: Engine,
) -> None:
    repository = PostgresSubjectPerformanceRepository(engine=engine)

    latest = repository.get_latest_subject_performance("930001")

    assert latest is not None
    assert tuple(subject.subject for subject in latest.strongest_subjects) == (
        "Mathematics",
        "History",
    )
    assert latest.strongest_subjects[0].source_version == "final"
    assert latest.strongest_subjects[0].entries_count_total == 26
    assert latest.strongest_subjects[0].high_grade_count == 18
    assert latest.strongest_subjects[0].high_grade_share_pct == pytest.approx(69.2308)
    assert latest.strongest_subjects[0].pass_grade_share_pct == pytest.approx(100.0)
    assert latest.weakest_subjects[0].subject == "History"
    assert latest.stage_breakdowns[0].key_stage == "ks4"
    assert latest.stage_breakdowns[0].exam_cohort is None
    assert latest.latest_updated_at is not None


def test_repository_returns_optional_16_to_18_groups_when_enabled(engine: Engine) -> None:
    repository = PostgresSubjectPerformanceRepository(engine=engine)

    latest = repository.get_latest_subject_performance("930001", include_16_to_18=True)
    series = repository.get_subject_performance_series("930001", include_16_to_18=True)

    assert latest is not None
    assert tuple(group.key_stage for group in latest.stage_breakdowns) == ("ks4", "16_to_18")
    assert latest.stage_breakdowns[1].exam_cohort == "A level"
    assert latest.stage_breakdowns[1].subjects[0].subject == "Physics"
    assert latest.stage_breakdowns[1].subjects[0].ranking_eligible is True

    assert series is not None
    assert tuple(group.key_stage for group in series.rows) == ("ks4", "16_to_18")
    assert series.rows[1].qualification_family == "a_level"
    assert series.rows[1].subjects[0].high_grade_share_pct == pytest.approx(100.0)


def test_repository_returns_none_for_unknown_or_empty_school(engine: Engine) -> None:
    repository = PostgresSubjectPerformanceRepository(engine=engine)

    assert repository.get_latest_subject_performance("999999") is None
    assert repository.get_subject_performance_series("999999") is None
    assert repository.get_latest_subject_performance("930002") is None
    assert repository.get_subject_performance_series("930002") is None
