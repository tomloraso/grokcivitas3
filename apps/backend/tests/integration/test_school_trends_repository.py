from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_school_trends_repository import (
    PostgresSchoolTrendsRepository,
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
    reason="Postgres database unavailable for school trends repository integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    engine = _build_engine(DATABASE_URL)
    _ensure_schema(engine)
    _seed_data(engine)
    try:
        yield engine
    finally:
        _cleanup_data(engine)
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
                CREATE TABLE IF NOT EXISTS school_demographics_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    disadvantaged_pct double precision NULL,
                    fsm_pct double precision NULL,
                    fsm6_pct double precision NULL,
                    sen_pct double precision NULL,
                    sen_support_pct double precision NULL,
                    ehcp_pct double precision NULL,
                    eal_pct double precision NULL,
                    first_language_english_pct double precision NULL,
                    first_language_unclassified_pct double precision NULL,
                    male_pct double precision NULL,
                    female_pct double precision NULL,
                    pupil_mobility_pct double precision NULL,
                    total_pupils integer NULL,
                    has_ethnicity_data boolean NOT NULL DEFAULT false,
                    has_top_languages_data boolean NOT NULL DEFAULT false,
                    has_fsm6_data boolean NOT NULL DEFAULT false,
                    has_gender_data boolean NOT NULL DEFAULT false,
                    has_mobility_data boolean NOT NULL DEFAULT false,
                    has_send_primary_need_data boolean NOT NULL DEFAULT false,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year)
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
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_behaviour_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    suspensions_count integer NULL,
                    suspensions_rate double precision NULL,
                    permanent_exclusions_count integer NULL,
                    permanent_exclusions_rate double precision NULL,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year)
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
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_performance_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    attainment8_average double precision NULL,
                    progress8_average double precision NULL,
                    progress8_disadvantaged double precision NULL,
                    progress8_not_disadvantaged double precision NULL,
                    progress8_disadvantaged_gap double precision NULL,
                    engmath_5_plus_pct double precision NULL,
                    engmath_4_plus_pct double precision NULL,
                    ebacc_entry_pct double precision NULL,
                    ebacc_5_plus_pct double precision NULL,
                    ebacc_4_plus_pct double precision NULL,
                    ks2_reading_expected_pct double precision NULL,
                    ks2_writing_expected_pct double precision NULL,
                    ks2_maths_expected_pct double precision NULL,
                    ks2_combined_expected_pct double precision NULL,
                    ks2_reading_higher_pct double precision NULL,
                    ks2_writing_higher_pct double precision NULL,
                    ks2_maths_higher_pct double precision NULL,
                    ks2_combined_higher_pct double precision NULL,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year)
                )
                """
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_performance_yearly "
                "ADD COLUMN IF NOT EXISTS source_dataset_id text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_performance_yearly "
                "ADD COLUMN IF NOT EXISTS source_dataset_version text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_performance_yearly "
                "ADD COLUMN IF NOT EXISTS updated_at timestamptz NULL"
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS postcode_cache (
                    postcode text PRIMARY KEY,
                    lat double precision NOT NULL,
                    lng double precision NOT NULL,
                    country_code text NULL,
                    region text NULL,
                    admin_district text NULL,
                    parliamentary_constituency text NULL,
                    lsoa_code text NULL,
                    msoa_code text NULL,
                    ward_code text NULL,
                    source text NOT NULL,
                    cached_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    expires_at timestamptz NOT NULL
                )
                """
            )
        )
        connection.execute(
            text("ALTER TABLE postcode_cache ADD COLUMN IF NOT EXISTS lat double precision NULL")
        )
        connection.execute(
            text("ALTER TABLE postcode_cache ADD COLUMN IF NOT EXISTS lng double precision NULL")
        )
        connection.execute(
            text("ALTER TABLE postcode_cache ADD COLUMN IF NOT EXISTS lsoa_code text NULL")
        )
        connection.execute(
            text("ALTER TABLE postcode_cache ADD COLUMN IF NOT EXISTS source text NULL")
        )
        connection.execute(
            text("ALTER TABLE postcode_cache ADD COLUMN IF NOT EXISTS cached_at timestamptz NULL")
        )
        connection.execute(
            text("ALTER TABLE postcode_cache ADD COLUMN IF NOT EXISTS expires_at timestamptz NULL")
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS area_deprivation (
                    lsoa_code text PRIMARY KEY,
                    lsoa_name text NOT NULL,
                    local_authority_district_code text NOT NULL,
                    local_authority_district_name text NOT NULL,
                    imd_score double precision NOT NULL,
                    imd_rank integer NOT NULL,
                    imd_decile integer NOT NULL,
                    idaci_score double precision NOT NULL,
                    idaci_decile integer NOT NULL,
                    population_total integer NULL,
                    source_release text NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS local_authority_district_code text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS local_authority_district_name text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS population_total integer NULL"
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
                    radius_meters integer NOT NULL,
                    source_archive_url text NOT NULL,
                    source_dataset_month text NOT NULL,
                    source_dataset_version text NULL,
                    source_file_url text NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, month, crime_category, radius_meters)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS area_house_price_context (
                    area_code text NOT NULL,
                    area_name text NOT NULL,
                    month date NOT NULL,
                    average_price double precision NOT NULL,
                    monthly_change_pct double precision NULL,
                    annual_change_pct double precision NULL,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    source_file_url text NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (area_code, month)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS metric_benchmarks_yearly (
                    metric_key text NOT NULL,
                    academic_year text NOT NULL,
                    benchmark_scope text NOT NULL,
                    benchmark_area text NOT NULL,
                    benchmark_label text NOT NULL,
                    benchmark_value double precision NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (metric_key, academic_year, benchmark_scope, benchmark_area)
                )
                """
            )
        )


def _seed_data(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn, name, phase, type, status, postcode,
                    easting, northing, location, capacity, pupil_count, open_date, close_date
                ) VALUES (
                    '920001',
                    'Trends Test School',
                    'Secondary',
                    'Academy',
                    'Open',
                    'SW1A 1AA',
                    0,
                    0,
                    ST_SetSRID(ST_MakePoint(-0.1416, 51.5010), 4326)::geography(Point, 4326),
                    700,
                    650,
                    '2004-09-01',
                    NULL
                )
                ON CONFLICT (urn) DO NOTHING
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn, name, phase, type, status, postcode,
                    easting, northing, location, capacity, pupil_count, open_date, close_date
                ) VALUES (
                    '920002',
                    'Trends Empty School',
                    'Primary',
                    'Community school',
                    'Open',
                    'SW1A 2AA',
                    0,
                    0,
                    ST_SetSRID(ST_MakePoint(-0.1415, 51.5011), 4326)::geography(Point, 4326),
                    350,
                    300,
                    '2008-09-01',
                    NULL
                )
                ON CONFLICT (urn) DO NOTHING
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_demographics_yearly (
                    urn,
                    academic_year,
                    disadvantaged_pct,
                    fsm_pct,
                    fsm6_pct,
                    sen_pct,
                    ehcp_pct,
                    eal_pct,
                    first_language_english_pct,
                    first_language_unclassified_pct,
                    male_pct,
                    female_pct,
                    pupil_mobility_pct,
                    source_dataset_id
                ) VALUES
                (
                    '920001',
                    '2024/25',
                    18.0,
                    16.9,
                    18.1,
                    12.0,
                    2.4,
                    9.1,
                    88.9,
                    0.7,
                    49.2,
                    50.8,
                    3.4,
                    'dataset-1'
                ),
                (
                    '920001',
                    '2023/24',
                    19.5,
                    17.4,
                    19.6,
                    11.5,
                    2.3,
                    8.8,
                    89.4,
                    0.6,
                    49.5,
                    50.5,
                    3.0,
                    'dataset-1'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    disadvantaged_pct = EXCLUDED.disadvantaged_pct,
                    fsm_pct = EXCLUDED.fsm_pct,
                    fsm6_pct = EXCLUDED.fsm6_pct,
                    sen_pct = EXCLUDED.sen_pct,
                    ehcp_pct = EXCLUDED.ehcp_pct,
                    eal_pct = EXCLUDED.eal_pct,
                    first_language_english_pct = EXCLUDED.first_language_english_pct,
                    first_language_unclassified_pct = EXCLUDED.first_language_unclassified_pct,
                    male_pct = EXCLUDED.male_pct,
                    female_pct = EXCLUDED.female_pct,
                    pupil_mobility_pct = EXCLUDED.pupil_mobility_pct
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_attendance_yearly (
                    urn,
                    academic_year,
                    overall_attendance_pct,
                    overall_absence_pct,
                    persistent_absence_pct,
                    source_dataset_id
                ) VALUES
                (
                    '920001',
                    '2023/24',
                    93.0,
                    7.0,
                    14.8,
                    'attendance-dataset'
                ),
                (
                    '920001',
                    '2024/25',
                    93.2,
                    6.8,
                    14.1,
                    'attendance-dataset'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    overall_attendance_pct = EXCLUDED.overall_attendance_pct,
                    overall_absence_pct = EXCLUDED.overall_absence_pct,
                    persistent_absence_pct = EXCLUDED.persistent_absence_pct
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_behaviour_yearly (
                    urn,
                    academic_year,
                    suspensions_count,
                    suspensions_rate,
                    permanent_exclusions_count,
                    permanent_exclusions_rate,
                    source_dataset_id
                ) VALUES
                (
                    '920001',
                    '2023/24',
                    109,
                    14.8,
                    1,
                    0.1,
                    'behaviour-dataset'
                ),
                (
                    '920001',
                    '2024/25',
                    121,
                    16.4,
                    1,
                    0.1,
                    'behaviour-dataset'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    suspensions_count = EXCLUDED.suspensions_count,
                    suspensions_rate = EXCLUDED.suspensions_rate,
                    permanent_exclusions_count = EXCLUDED.permanent_exclusions_count,
                    permanent_exclusions_rate = EXCLUDED.permanent_exclusions_rate
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_workforce_yearly (
                    urn,
                    academic_year,
                    pupil_teacher_ratio,
                    supply_staff_pct,
                    teachers_3plus_years_pct,
                    teacher_turnover_pct,
                    qts_pct,
                    qualifications_level6_plus_pct,
                    source_dataset_id
                ) VALUES
                (
                    '920001',
                    '2023/24',
                    16.7,
                    2.8,
                    74.0,
                    10.2,
                    95.1,
                    80.3,
                    'workforce-dataset'
                ),
                (
                    '920001',
                    '2024/25',
                    16.3,
                    2.4,
                    76.5,
                    9.8,
                    95.2,
                    81.1,
                    'workforce-dataset'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    pupil_teacher_ratio = EXCLUDED.pupil_teacher_ratio,
                    supply_staff_pct = EXCLUDED.supply_staff_pct,
                    teachers_3plus_years_pct = EXCLUDED.teachers_3plus_years_pct,
                    teacher_turnover_pct = EXCLUDED.teacher_turnover_pct,
                    qts_pct = EXCLUDED.qts_pct,
                    qualifications_level6_plus_pct = EXCLUDED.qualifications_level6_plus_pct
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn, name, phase, type, status, postcode,
                    easting, northing, location, capacity, pupil_count, open_date, close_date
                ) VALUES (
                    '920003',
                    'Trends Benchmark Peer School',
                    'Secondary',
                    'Academy',
                    'Open',
                    'SW1A 3AA',
                    0,
                    0,
                    ST_SetSRID(ST_MakePoint(-0.1412, 51.5012), 4326)::geography(Point, 4326),
                    680,
                    640,
                    '2007-09-01',
                    NULL
                )
                ON CONFLICT (urn) DO NOTHING
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_demographics_yearly (
                    urn,
                    academic_year,
                    disadvantaged_pct,
                    fsm_pct,
                    fsm6_pct,
                    sen_pct,
                    ehcp_pct,
                    eal_pct,
                    first_language_english_pct,
                    first_language_unclassified_pct,
                    male_pct,
                    female_pct,
                    pupil_mobility_pct,
                    source_dataset_id
                ) VALUES
                ('920003', '2023/24', 15.0, 14.0, 16.0, 10.1, 2.0, 7.8, 90.0, 0.5, 50.1, 49.9, 2.8, 'dataset-1'),
                ('920003', '2024/25', 16.0, 15.0, 17.0, 10.3, 2.1, 8.0, 89.7, 0.5, 50.0, 50.0, 2.9, 'dataset-1')
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    disadvantaged_pct = EXCLUDED.disadvantaged_pct,
                    fsm_pct = EXCLUDED.fsm_pct,
                    fsm6_pct = EXCLUDED.fsm6_pct
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_attendance_yearly (
                    urn,
                    academic_year,
                    overall_attendance_pct,
                    overall_absence_pct,
                    persistent_absence_pct,
                    source_dataset_id
                ) VALUES
                ('920003', '2023/24', 92.4, 7.6, 15.8, 'attendance-dataset'),
                ('920003', '2024/25', 92.8, 7.2, 15.0, 'attendance-dataset')
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    overall_attendance_pct = EXCLUDED.overall_attendance_pct,
                    overall_absence_pct = EXCLUDED.overall_absence_pct,
                    persistent_absence_pct = EXCLUDED.persistent_absence_pct
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_behaviour_yearly (
                    urn,
                    academic_year,
                    suspensions_count,
                    suspensions_rate,
                    permanent_exclusions_count,
                    permanent_exclusions_rate,
                    source_dataset_id
                ) VALUES
                ('920003', '2023/24', 88, 12.4, 1, 0.2, 'behaviour-dataset'),
                ('920003', '2024/25', 93, 12.8, 1, 0.2, 'behaviour-dataset')
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    suspensions_count = EXCLUDED.suspensions_count,
                    suspensions_rate = EXCLUDED.suspensions_rate,
                    permanent_exclusions_count = EXCLUDED.permanent_exclusions_count,
                    permanent_exclusions_rate = EXCLUDED.permanent_exclusions_rate
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_workforce_yearly (
                    urn,
                    academic_year,
                    pupil_teacher_ratio,
                    supply_staff_pct,
                    teachers_3plus_years_pct,
                    teacher_turnover_pct,
                    qts_pct,
                    qualifications_level6_plus_pct,
                    source_dataset_id
                ) VALUES
                ('920003', '2023/24', 16.9, 2.6, 75.2, 10.0, 95.4, 81.2, 'workforce-dataset'),
                ('920003', '2024/25', 16.6, 2.5, 75.9, 9.5, 95.7, 82.0, 'workforce-dataset')
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    pupil_teacher_ratio = EXCLUDED.pupil_teacher_ratio,
                    supply_staff_pct = EXCLUDED.supply_staff_pct,
                    teachers_3plus_years_pct = EXCLUDED.teachers_3plus_years_pct,
                    teacher_turnover_pct = EXCLUDED.teacher_turnover_pct,
                    qts_pct = EXCLUDED.qts_pct,
                    qualifications_level6_plus_pct = EXCLUDED.qualifications_level6_plus_pct
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_performance_yearly (
                    urn,
                    academic_year,
                    attainment8_average,
                    progress8_average,
                    progress8_disadvantaged_gap,
                    engmath_5_plus_pct,
                    ebacc_entry_pct,
                    source_dataset_id
                ) VALUES
                ('920001', '2024/25', 55.2, 0.35, 0.14, 64.1, 41.5, 'performance-dataset'),
                ('920003', '2024/25', 51.8, 0.12, 0.20, 59.7, 38.1, 'performance-dataset')
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    attainment8_average = EXCLUDED.attainment8_average,
                    progress8_average = EXCLUDED.progress8_average,
                    progress8_disadvantaged_gap = EXCLUDED.progress8_disadvantaged_gap,
                    engmath_5_plus_pct = EXCLUDED.engmath_5_plus_pct,
                    ebacc_entry_pct = EXCLUDED.ebacc_entry_pct
                """
            )
        )


def _cleanup_data(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM metric_benchmarks_yearly"))
        connection.execute(
            text("DELETE FROM area_house_price_context WHERE area_code IN ('E09000033')")
        )
        connection.execute(
            text("DELETE FROM area_crime_context WHERE urn IN ('920001', '920002', '920003')")
        )
        connection.execute(
            text(
                "DELETE FROM school_performance_yearly WHERE urn IN ('920001', '920002', '920003')"
            )
        )
        connection.execute(
            text("DELETE FROM school_workforce_yearly WHERE urn IN ('920001', '920002', '920003')")
        )
        connection.execute(
            text("DELETE FROM school_behaviour_yearly WHERE urn IN ('920001', '920002', '920003')")
        )
        connection.execute(
            text("DELETE FROM school_attendance_yearly WHERE urn IN ('920001', '920002', '920003')")
        )
        connection.execute(
            text(
                "DELETE FROM school_demographics_yearly WHERE urn IN ('920001', '920002', '920003')"
            )
        )
        connection.execute(
            text("DELETE FROM area_deprivation WHERE lsoa_code IN ('E01004736', 'E01004737')")
        )
        connection.execute(
            text("DELETE FROM postcode_cache WHERE postcode IN ('SW1A1AA', 'SW1A3AA')")
        )
        connection.execute(text("DELETE FROM schools WHERE urn IN ('920001', '920002', '920003')"))


def test_school_trends_repository_returns_demographics_ordered_by_academic_year(
    engine: Engine,
) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    demographics = repository.get_demographics_series("920001")
    assert demographics is not None
    assert demographics.urn == "920001"
    assert [row.academic_year for row in demographics.rows] == ["2023/24", "2024/25"]
    assert demographics.rows[0].disadvantaged_pct == 19.5
    assert demographics.rows[1].disadvantaged_pct == 18.0
    assert demographics.rows[0].fsm_pct == 17.4
    assert demographics.rows[1].fsm6_pct == 18.1
    assert demographics.rows[0].first_language_english_pct == 89.4
    assert demographics.rows[1].first_language_unclassified_pct == 0.7
    assert demographics.rows[1].male_pct == 49.2
    assert demographics.rows[1].female_pct == 50.8
    assert demographics.rows[1].pupil_mobility_pct == 3.4
    assert demographics.latest_updated_at is not None

    attendance = repository.get_attendance_series("920001")
    assert attendance is not None
    assert [row.academic_year for row in attendance.rows] == ["2023/24", "2024/25"]
    assert attendance.rows[0].overall_attendance_pct == 93.0
    assert attendance.rows[1].overall_absence_pct == 6.8
    assert attendance.rows[1].persistent_absence_pct == 14.1
    assert attendance.latest_updated_at is not None

    behaviour = repository.get_behaviour_series("920001")
    assert behaviour is not None
    assert [row.academic_year for row in behaviour.rows] == ["2023/24", "2024/25"]
    assert behaviour.rows[0].suspensions_count == 109
    assert behaviour.rows[1].suspensions_rate == 16.4
    assert behaviour.rows[1].permanent_exclusions_count == 1
    assert behaviour.rows[1].permanent_exclusions_rate == 0.1
    assert behaviour.latest_updated_at is not None

    workforce = repository.get_workforce_series("920001")
    assert workforce is not None
    assert [row.academic_year for row in workforce.rows] == ["2023/24", "2024/25"]
    assert workforce.rows[0].pupil_teacher_ratio == 16.7
    assert workforce.rows[1].supply_staff_pct == 2.4
    assert workforce.rows[1].teachers_3plus_years_pct == 76.5
    assert workforce.rows[1].teacher_turnover_pct == 9.8
    assert workforce.rows[1].qts_pct == 95.2
    assert workforce.rows[1].qualifications_level6_plus_pct == 81.1
    assert workforce.latest_updated_at is not None


def test_school_trends_repository_returns_metric_benchmarks_and_persists_snapshot(
    engine: Engine,
) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    benchmarks = repository.get_metric_benchmark_series("920001")
    assert benchmarks is not None
    assert benchmarks.urn == "920001"

    by_metric_year = {(row.metric_key, row.academic_year): row for row in benchmarks.rows}
    fsm_2024 = by_metric_year[("fsm_pct", "2024/25")]
    assert fsm_2024.school_value == pytest.approx(16.9)
    assert fsm_2024.national_value is not None
    assert 0.0 <= fsm_2024.national_value <= 100.0
    assert fsm_2024.local_value is not None
    assert 0.0 <= fsm_2024.local_value <= 100.0
    assert fsm_2024.local_scope == "phase"
    assert fsm_2024.local_area_code == "Secondary"
    assert fsm_2024.local_area_label == "Secondary"

    with engine.connect() as connection:
        persisted_rows = (
            connection.execute(
                text(
                    """
                SELECT benchmark_scope, benchmark_area, benchmark_value
                FROM metric_benchmarks_yearly
                WHERE metric_key = 'fsm_pct' AND academic_year = '2024/25'
                ORDER BY benchmark_scope, benchmark_area
                """
                )
            )
            .mappings()
            .all()
        )

    assert len(persisted_rows) == 2
    scopes = {str(row["benchmark_scope"]) for row in persisted_rows}
    assert scopes == {"national", "phase"}

    with engine.connect() as connection:
        null_rows = (
            connection.execute(
                text(
                    """
                SELECT benchmark_scope, benchmark_area, benchmark_value
                FROM metric_benchmarks_yearly
                WHERE metric_key = 'progress8_disadvantaged' AND academic_year = '2024/25'
                ORDER BY benchmark_scope, benchmark_area
                """
                )
            )
            .mappings()
            .all()
        )

    assert len(null_rows) == 2
    assert {str(row["benchmark_scope"]) for row in null_rows} == {"national", "phase"}
    assert all(row["benchmark_value"] is None for row in null_rows)


def test_school_trends_repository_reuses_cached_metric_benchmarks(engine: Engine) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    seeded = repository.get_metric_benchmark_series("920001")
    assert seeded is not None

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO metric_benchmarks_yearly (
                    metric_key,
                    academic_year,
                    benchmark_scope,
                    benchmark_area,
                    benchmark_label,
                    benchmark_value
                ) VALUES
                ('fsm_pct', '2024/25', 'national', 'england', 'England', 42.0),
                ('fsm_pct', '2024/25', 'phase', 'Secondary', 'Secondary', 24.0)
                ON CONFLICT (metric_key, academic_year, benchmark_scope, benchmark_area)
                DO UPDATE SET
                    benchmark_label = EXCLUDED.benchmark_label,
                    benchmark_value = EXCLUDED.benchmark_value
                """
            )
        )

    benchmarks = repository.get_metric_benchmark_series("920001")

    assert benchmarks is not None
    by_metric_year = {(row.metric_key, row.academic_year): row for row in benchmarks.rows}
    fsm_2024 = by_metric_year[("fsm_pct", "2024/25")]
    assert fsm_2024.school_value == pytest.approx(16.9)
    assert fsm_2024.national_value == pytest.approx(42.0)
    assert fsm_2024.local_value == pytest.approx(24.0)
    assert fsm_2024.local_scope == "phase"
    assert fsm_2024.local_area_code == "Secondary"
    assert fsm_2024.local_area_label == "Secondary"

    progress8_disadvantaged_2024 = by_metric_year[("progress8_disadvantaged", "2024/25")]
    assert progress8_disadvantaged_2024.national_value is None
    assert progress8_disadvantaged_2024.local_value is None


def test_school_trends_repository_recomputes_when_cached_snapshot_is_partial(
    engine: Engine,
) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    baseline = repository.get_metric_benchmark_series("920001")
    assert baseline is not None
    baseline_by_metric_year = {
        (row.metric_key, row.academic_year): (row.national_value, row.local_value)
        for row in baseline.rows
    }

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM metric_benchmarks_yearly"))
        connection.execute(
            text(
                """
                INSERT INTO metric_benchmarks_yearly (
                    metric_key,
                    academic_year,
                    benchmark_scope,
                    benchmark_area,
                    benchmark_label,
                    benchmark_value
                ) VALUES
                ('fsm_pct', '2024/25', 'national', 'england', 'England', 42.0),
                ('fsm_pct', '2024/25', 'phase', 'Secondary', 'Secondary', 24.0)
                ON CONFLICT (metric_key, academic_year, benchmark_scope, benchmark_area)
                DO UPDATE SET
                    benchmark_label = EXCLUDED.benchmark_label,
                    benchmark_value = EXCLUDED.benchmark_value
                """
            )
        )

    benchmarks = repository.get_metric_benchmark_series("920001")

    assert benchmarks is not None
    by_metric_year = {(row.metric_key, row.academic_year): row for row in benchmarks.rows}

    fsm_2024 = by_metric_year[("fsm_pct", "2024/25")]
    assert (
        fsm_2024.national_value,
        fsm_2024.local_value,
    ) == baseline_by_metric_year[("fsm_pct", "2024/25")]
    assert (fsm_2024.national_value, fsm_2024.local_value) != (42.0, 24.0)

    attendance_2024 = by_metric_year[("overall_attendance_pct", "2024/25")]
    assert (
        attendance_2024.national_value,
        attendance_2024.local_value,
    ) == baseline_by_metric_year[("overall_attendance_pct", "2024/25")]

    with engine.connect() as connection:
        benchmark_count = connection.execute(
            text("SELECT count(*) FROM metric_benchmarks_yearly")
        ).scalar_one()

    assert benchmark_count > 2


def test_school_trends_repository_returns_empty_rows_for_school_without_history(
    engine: Engine,
) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    demographics = repository.get_demographics_series("920002")
    attendance = repository.get_attendance_series("920002")
    behaviour = repository.get_behaviour_series("920002")
    workforce = repository.get_workforce_series("920002")

    assert demographics is not None
    assert demographics.urn == "920002"
    assert demographics.rows == ()
    assert demographics.latest_updated_at is None

    assert attendance is not None
    assert attendance.urn == "920002"
    assert attendance.rows == ()
    assert attendance.latest_updated_at is None

    assert behaviour is not None
    assert behaviour.urn == "920002"
    assert behaviour.rows == ()
    assert behaviour.latest_updated_at is None

    assert workforce is not None
    assert workforce.urn == "920002"
    assert workforce.rows == ()
    assert workforce.latest_updated_at is None


def test_school_trends_repository_returns_none_for_unknown_school(engine: Engine) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    demographics = repository.get_demographics_series("999999")
    attendance = repository.get_attendance_series("999999")
    behaviour = repository.get_behaviour_series("999999")
    workforce = repository.get_workforce_series("999999")
    benchmarks = repository.get_metric_benchmark_series("999999")

    assert demographics is None
    assert attendance is None
    assert behaviour is None
    assert workforce is None
    assert benchmarks is None
