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
        for statement in (
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_headcount_total double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_fte_total double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS support_staff_headcount_total double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS support_staff_fte_total double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS leadership_headcount double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS leadership_share_of_teachers double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_average_mean_salary_gbp double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_average_median_salary_gbp double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teachers_on_leadership_pay_range_pct double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_absence_pct double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_absence_days_total double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_absence_days_average double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_absence_days_average_all_teachers double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_vacancy_count double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_vacancy_rate double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_tempfilled_vacancy_count double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS teacher_tempfilled_vacancy_rate double precision NULL",
            "ALTER TABLE school_workforce_yearly "
            "ADD COLUMN IF NOT EXISTS third_party_support_staff_headcount double precision NULL",
        ):
            connection.execute(text(statement))
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_financials_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    finance_source text NOT NULL DEFAULT 'aar',
                    school_laestab text NULL,
                    school_name text NOT NULL,
                    trust_uid text NULL,
                    trust_name text NULL,
                    phase text NULL,
                    overall_phase text NULL,
                    admissions_policy text NULL,
                    urban_rural text NULL,
                    pupils_fte double precision NULL,
                    teachers_fte double precision NULL,
                    fsm_pct double precision NULL,
                    ehcp_pct double precision NULL,
                    sen_support_pct double precision NULL,
                    eal_pct double precision NULL,
                    total_grant_funding_gbp double precision NULL,
                    total_self_generated_funding_gbp double precision NULL,
                    total_income_gbp double precision NULL,
                    teaching_staff_costs_gbp double precision NULL,
                    supply_teaching_staff_costs_gbp double precision NULL,
                    education_support_staff_costs_gbp double precision NULL,
                    other_staff_costs_gbp double precision NULL,
                    total_staff_costs_gbp double precision NULL,
                    maintenance_improvement_costs_gbp double precision NULL,
                    premises_costs_gbp double precision NULL,
                    educational_supplies_costs_gbp double precision NULL,
                    bought_in_professional_services_costs_gbp double precision NULL,
                    catering_costs_gbp double precision NULL,
                    total_expenditure_gbp double precision NULL,
                    revenue_reserve_gbp double precision NULL,
                    in_year_balance_gbp double precision NULL,
                    income_per_pupil_gbp double precision NULL,
                    expenditure_per_pupil_gbp double precision NULL,
                    staff_costs_pct_of_expenditure double precision NULL,
                    teaching_staff_costs_per_pupil_gbp double precision NULL,
                    supply_staff_costs_pct_of_staff_costs double precision NULL,
                    revenue_reserve_per_pupil_gbp double precision NULL,
                    source_file_url text NOT NULL,
                    source_updated_at_utc timestamptz NOT NULL,
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
                INSERT INTO school_financials_yearly (
                    urn,
                    academic_year,
                    finance_source,
                    school_laestab,
                    school_name,
                    trust_uid,
                    trust_name,
                    phase,
                    overall_phase,
                    admissions_policy,
                    urban_rural,
                    pupils_fte,
                    teachers_fte,
                    fsm_pct,
                    ehcp_pct,
                    sen_support_pct,
                    eal_pct,
                    total_grant_funding_gbp,
                    total_self_generated_funding_gbp,
                    total_income_gbp,
                    teaching_staff_costs_gbp,
                    supply_teaching_staff_costs_gbp,
                    education_support_staff_costs_gbp,
                    other_staff_costs_gbp,
                    total_staff_costs_gbp,
                    maintenance_improvement_costs_gbp,
                    premises_costs_gbp,
                    educational_supplies_costs_gbp,
                    bought_in_professional_services_costs_gbp,
                    catering_costs_gbp,
                    total_expenditure_gbp,
                    revenue_reserve_gbp,
                    in_year_balance_gbp,
                    income_per_pupil_gbp,
                    expenditure_per_pupil_gbp,
                    staff_costs_pct_of_expenditure,
                    teaching_staff_costs_per_pupil_gbp,
                    supply_staff_costs_pct_of_staff_costs,
                    revenue_reserve_per_pupil_gbp,
                    source_file_url,
                    source_updated_at_utc
                ) VALUES
                (
                    '920001',
                    '2023/24',
                    'aar',
                    '213/6007',
                    'Trends Test School',
                    '5712',
                    'Example Trust',
                    'Secondary',
                    'Secondary',
                    'Comprehensive',
                    'Urban major conurbation',
                    650.0,
                    42.0,
                    16.8,
                    2.0,
                    11.9,
                    8.6,
                    4020000.0,
                    220000.0,
                    4240000.0,
                    2100000.0,
                    52000.0,
                    640000.0,
                    315000.0,
                    3107000.0,
                    160000.0,
                    210000.0,
                    98000.0,
                    74000.0,
                    92000.0,
                    4085000.0,
                    525000.0,
                    155000.0,
                    6523.08,
                    6284.62,
                    0.7606,
                    3230.77,
                    0.0167,
                    807.69,
                    'https://example.com/AAR_2023-24_download.xlsx',
                    '2026-03-10T10:00:00+00:00'
                ),
                (
                    '920001',
                    '2024/25',
                    'aar',
                    '213/6007',
                    'Trends Test School',
                    '5712',
                    'Example Trust',
                    'Secondary',
                    'Secondary',
                    'Comprehensive',
                    'Urban major conurbation',
                    660.0,
                    43.0,
                    16.9,
                    2.1,
                    12.0,
                    8.8,
                    4150000.0,
                    240000.0,
                    4390000.0,
                    2190000.0,
                    55000.0,
                    670000.0,
                    330000.0,
                    3245000.0,
                    168000.0,
                    220000.0,
                    102000.0,
                    76000.0,
                    94000.0,
                    4210000.0,
                    560000.0,
                    180000.0,
                    6651.52,
                    6378.79,
                    0.7708,
                    3318.18,
                    0.0169,
                    848.48,
                    'https://example.com/AAR_2024-25_download.xlsx',
                    '2026-03-10T10:00:00+00:00'
                ),
                (
                    '920003',
                    '2023/24',
                    'aar',
                    '213/6009',
                    'Trends Benchmark Peer School',
                    '5714',
                    'Example Trust',
                    'Secondary',
                    'Secondary',
                    'Comprehensive',
                    'Urban major conurbation',
                    640.0,
                    41.0,
                    15.2,
                    1.9,
                    10.9,
                    7.9,
                    3890000.0,
                    205000.0,
                    4095000.0,
                    2015000.0,
                    50000.0,
                    620000.0,
                    300000.0,
                    2985000.0,
                    154000.0,
                    205000.0,
                    94000.0,
                    70000.0,
                    88000.0,
                    3960000.0,
                    490000.0,
                    135000.0,
                    6398.44,
                    6187.50,
                    0.7548,
                    3148.44,
                    0.0168,
                    765.62,
                    'https://example.com/AAR_2023-24_download.xlsx',
                    '2026-03-10T10:00:00+00:00'
                ),
                (
                    '920003',
                    '2024/25',
                    'aar',
                    '213/6009',
                    'Trends Benchmark Peer School',
                    '5714',
                    'Example Trust',
                    'Secondary',
                    'Secondary',
                    'Comprehensive',
                    'Urban major conurbation',
                    645.0,
                    41.5,
                    15.0,
                    2.0,
                    10.8,
                    8.0,
                    3940000.0,
                    210000.0,
                    4150000.0,
                    2050000.0,
                    51000.0,
                    635000.0,
                    306000.0,
                    3042000.0,
                    158000.0,
                    208000.0,
                    96000.0,
                    71500.0,
                    90000.0,
                    4025000.0,
                    505000.0,
                    125000.0,
                    6434.11,
                    6240.31,
                    0.7558,
                    3178.29,
                    0.0168,
                    782.95,
                    'https://example.com/AAR_2024-25_download.xlsx',
                    '2026-03-10T10:00:00+00:00'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    total_income_gbp = EXCLUDED.total_income_gbp,
                    total_expenditure_gbp = EXCLUDED.total_expenditure_gbp,
                    income_per_pupil_gbp = EXCLUDED.income_per_pupil_gbp,
                    expenditure_per_pupil_gbp = EXCLUDED.expenditure_per_pupil_gbp,
                    staff_costs_pct_of_expenditure = EXCLUDED.staff_costs_pct_of_expenditure,
                    teaching_staff_costs_per_pupil_gbp = EXCLUDED.teaching_staff_costs_per_pupil_gbp,
                    revenue_reserve_per_pupil_gbp = EXCLUDED.revenue_reserve_per_pupil_gbp
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
                    teacher_headcount_total,
                    teacher_fte_total,
                    support_staff_headcount_total,
                    support_staff_fte_total,
                    leadership_headcount,
                    leadership_share_of_teachers,
                    teacher_average_mean_salary_gbp,
                    teacher_average_median_salary_gbp,
                    teachers_on_leadership_pay_range_pct,
                    teacher_absence_pct,
                    teacher_absence_days_total,
                    teacher_absence_days_average,
                    teacher_absence_days_average_all_teachers,
                    teacher_vacancy_count,
                    teacher_vacancy_rate,
                    teacher_tempfilled_vacancy_count,
                    teacher_tempfilled_vacancy_rate,
                    third_party_support_staff_headcount,
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
                    41.0,
                    38.7,
                    27.0,
                    21.0,
                    4.0,
                    9.5,
                    45800.0,
                    44250.0,
                    6.8,
                    9.1,
                    214.0,
                    5.8,
                    5.2,
                    1.0,
                    2.0,
                    2.0,
                    4.0,
                    2.0,
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
                    42.0,
                    39.5,
                    28.0,
                    22.4,
                    4.0,
                    9.5,
                    46850.0,
                    45200.0,
                    7.1,
                    8.6,
                    198.0,
                    5.5,
                    4.7,
                    1.0,
                    1.7,
                    2.0,
                    3.4,
                    3.0,
                    'workforce-dataset'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    pupil_teacher_ratio = EXCLUDED.pupil_teacher_ratio,
                    supply_staff_pct = EXCLUDED.supply_staff_pct,
                    teachers_3plus_years_pct = EXCLUDED.teachers_3plus_years_pct,
                    teacher_turnover_pct = EXCLUDED.teacher_turnover_pct,
                    qts_pct = EXCLUDED.qts_pct,
                    qualifications_level6_plus_pct = EXCLUDED.qualifications_level6_plus_pct,
                    teacher_headcount_total = EXCLUDED.teacher_headcount_total,
                    teacher_fte_total = EXCLUDED.teacher_fte_total,
                    support_staff_headcount_total = EXCLUDED.support_staff_headcount_total,
                    support_staff_fte_total = EXCLUDED.support_staff_fte_total,
                    leadership_headcount = EXCLUDED.leadership_headcount,
                    leadership_share_of_teachers = EXCLUDED.leadership_share_of_teachers,
                    teacher_average_mean_salary_gbp = EXCLUDED.teacher_average_mean_salary_gbp,
                    teacher_average_median_salary_gbp = EXCLUDED.teacher_average_median_salary_gbp,
                    teachers_on_leadership_pay_range_pct = EXCLUDED.teachers_on_leadership_pay_range_pct,
                    teacher_absence_pct = EXCLUDED.teacher_absence_pct,
                    teacher_absence_days_total = EXCLUDED.teacher_absence_days_total,
                    teacher_absence_days_average = EXCLUDED.teacher_absence_days_average,
                    teacher_absence_days_average_all_teachers = EXCLUDED.teacher_absence_days_average_all_teachers,
                    teacher_vacancy_count = EXCLUDED.teacher_vacancy_count,
                    teacher_vacancy_rate = EXCLUDED.teacher_vacancy_rate,
                    teacher_tempfilled_vacancy_count = EXCLUDED.teacher_tempfilled_vacancy_count,
                    teacher_tempfilled_vacancy_rate = EXCLUDED.teacher_tempfilled_vacancy_rate,
                    third_party_support_staff_headcount = EXCLUDED.third_party_support_staff_headcount
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
                    teacher_headcount_total,
                    teacher_fte_total,
                    support_staff_headcount_total,
                    support_staff_fte_total,
                    leadership_headcount,
                    leadership_share_of_teachers,
                    teacher_average_mean_salary_gbp,
                    teacher_average_median_salary_gbp,
                    teachers_on_leadership_pay_range_pct,
                    teacher_absence_pct,
                    teacher_absence_days_total,
                    teacher_absence_days_average,
                    teacher_absence_days_average_all_teachers,
                    teacher_vacancy_count,
                    teacher_vacancy_rate,
                    teacher_tempfilled_vacancy_count,
                    teacher_tempfilled_vacancy_rate,
                    third_party_support_staff_headcount,
                    source_dataset_id
                ) VALUES
                ('920003', '2023/24', 16.9, 2.6, 75.2, 10.0, 95.4, 81.2, 40.0, 37.5, 26.0, 20.8, 4.0, 10.0, 45200.0, 43950.0, 6.5, 9.4, 205.0, 5.6, 5.0, 1.0, 2.1, 2.0, 4.2, 2.0, 'workforce-dataset'),
                ('920003', '2024/25', 16.6, 2.5, 75.9, 9.5, 95.7, 82.0, 41.0, 38.2, 27.0, 21.2, 4.0, 9.8, 45950.0, 44500.0, 6.9, 8.9, 201.0, 5.4, 4.9, 1.0, 1.9, 2.0, 3.8, 2.0, 'workforce-dataset')
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    pupil_teacher_ratio = EXCLUDED.pupil_teacher_ratio,
                    supply_staff_pct = EXCLUDED.supply_staff_pct,
                    teachers_3plus_years_pct = EXCLUDED.teachers_3plus_years_pct,
                    teacher_turnover_pct = EXCLUDED.teacher_turnover_pct,
                    qts_pct = EXCLUDED.qts_pct,
                    qualifications_level6_plus_pct = EXCLUDED.qualifications_level6_plus_pct,
                    teacher_headcount_total = EXCLUDED.teacher_headcount_total,
                    teacher_fte_total = EXCLUDED.teacher_fte_total,
                    support_staff_headcount_total = EXCLUDED.support_staff_headcount_total,
                    support_staff_fte_total = EXCLUDED.support_staff_fte_total,
                    leadership_headcount = EXCLUDED.leadership_headcount,
                    leadership_share_of_teachers = EXCLUDED.leadership_share_of_teachers,
                    teacher_average_mean_salary_gbp = EXCLUDED.teacher_average_mean_salary_gbp,
                    teacher_average_median_salary_gbp = EXCLUDED.teacher_average_median_salary_gbp,
                    teachers_on_leadership_pay_range_pct = EXCLUDED.teachers_on_leadership_pay_range_pct,
                    teacher_absence_pct = EXCLUDED.teacher_absence_pct,
                    teacher_absence_days_total = EXCLUDED.teacher_absence_days_total,
                    teacher_absence_days_average = EXCLUDED.teacher_absence_days_average,
                    teacher_absence_days_average_all_teachers = EXCLUDED.teacher_absence_days_average_all_teachers,
                    teacher_vacancy_count = EXCLUDED.teacher_vacancy_count,
                    teacher_vacancy_rate = EXCLUDED.teacher_vacancy_rate,
                    teacher_tempfilled_vacancy_count = EXCLUDED.teacher_tempfilled_vacancy_count,
                    teacher_tempfilled_vacancy_rate = EXCLUDED.teacher_tempfilled_vacancy_rate,
                    third_party_support_staff_headcount = EXCLUDED.third_party_support_staff_headcount
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
            text("DELETE FROM school_financials_yearly WHERE urn IN ('920001', '920002', '920003')")
        )
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
    assert workforce.rows[1].teacher_headcount_total == pytest.approx(42.0)
    assert workforce.rows[1].teacher_fte_total == pytest.approx(39.5)
    assert workforce.rows[1].support_staff_headcount_total == pytest.approx(28.0)
    assert workforce.rows[1].support_staff_fte_total == pytest.approx(22.4)
    assert workforce.rows[1].leadership_share_of_teachers == pytest.approx(9.5)
    assert workforce.rows[1].teacher_average_mean_salary_gbp == pytest.approx(46850.0)
    assert workforce.rows[1].teacher_average_median_salary_gbp == pytest.approx(45200.0)
    assert workforce.rows[1].teachers_on_leadership_pay_range_pct == pytest.approx(7.1)
    assert workforce.rows[1].teacher_absence_pct == pytest.approx(8.6)
    assert workforce.rows[1].teacher_absence_days_total == pytest.approx(198.0)
    assert workforce.rows[1].teacher_absence_days_average == pytest.approx(5.5)
    assert workforce.rows[1].teacher_absence_days_average_all_teachers == pytest.approx(4.7)
    assert workforce.rows[1].teacher_vacancy_count == pytest.approx(1.0)
    assert workforce.rows[1].teacher_vacancy_rate == pytest.approx(1.7)
    assert workforce.rows[1].teacher_tempfilled_vacancy_count == pytest.approx(2.0)
    assert workforce.rows[1].teacher_tempfilled_vacancy_rate == pytest.approx(3.4)
    assert workforce.rows[1].third_party_support_staff_headcount == pytest.approx(3.0)
    assert workforce.latest_updated_at is not None

    finance = repository.get_finance_series("920001")
    assert finance is not None
    assert finance.is_applicable is True
    assert [row.academic_year for row in finance.rows] == ["2023/24", "2024/25"]
    assert finance.rows[0].total_income_gbp == pytest.approx(4240000.0)
    assert finance.rows[1].income_per_pupil_gbp == pytest.approx(6651.52)
    assert finance.rows[1].staff_costs_pct_of_expenditure == pytest.approx(0.7708)
    assert finance.rows[1].revenue_reserve_per_pupil_gbp == pytest.approx(848.48)
    assert finance.latest_updated_at is not None


def test_school_trends_repository_returns_partial_metric_benchmarks_without_persisting_on_miss(
    engine: Engine,
) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM metric_benchmarks_yearly"))

    benchmarks = repository.get_metric_benchmark_series("920001")
    assert benchmarks is not None
    assert benchmarks.urn == "920001"

    by_metric_year = {(row.metric_key, row.academic_year): row for row in benchmarks.rows}
    fsm_2024 = by_metric_year[("fsm_pct", "2024/25")]
    assert fsm_2024.school_value == pytest.approx(16.9)
    assert fsm_2024.national_value is None
    assert fsm_2024.local_value is None
    assert fsm_2024.local_scope == "phase"
    assert fsm_2024.local_area_code == "Secondary"
    assert fsm_2024.local_area_label == "Secondary"

    finance_income_2024 = by_metric_year[("finance_income_per_pupil_gbp", "2024/25")]
    assert finance_income_2024.school_value == pytest.approx(6651.52)
    assert finance_income_2024.national_value is None
    assert finance_income_2024.local_value is None

    teacher_headcount_2024 = by_metric_year[("teacher_headcount_total", "2024/25")]
    assert teacher_headcount_2024.school_value == pytest.approx(42.0)
    assert teacher_headcount_2024.national_value is None
    assert teacher_headcount_2024.local_value is None

    vacancy_rate_2024 = by_metric_year[("teacher_vacancy_rate", "2024/25")]
    assert vacancy_rate_2024.school_value == pytest.approx(1.7)
    assert vacancy_rate_2024.local_scope == "phase"
    assert vacancy_rate_2024.local_area_label == "Secondary"

    with engine.connect() as connection:
        benchmark_count = connection.execute(
            text("SELECT count(*) FROM metric_benchmarks_yearly")
        ).scalar_one()

    assert benchmark_count == 0


def test_school_trends_repository_reuses_cached_metric_benchmarks(engine: Engine) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

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
    assert fsm_2024.school_value == pytest.approx(16.9)
    assert fsm_2024.national_value == pytest.approx(42.0)
    assert fsm_2024.local_value == pytest.approx(24.0)
    assert fsm_2024.local_scope == "phase"
    assert fsm_2024.local_area_code == "Secondary"
    assert fsm_2024.local_area_label == "Secondary"

    progress8_disadvantaged_2024 = by_metric_year[("progress8_disadvantaged", "2024/25")]
    assert progress8_disadvantaged_2024.national_value is None
    assert progress8_disadvantaged_2024.local_value is None

    finance_income_2024 = by_metric_year[("finance_income_per_pupil_gbp", "2024/25")]
    assert finance_income_2024.national_value is None
    assert finance_income_2024.local_value is None


def test_school_trends_repository_recomputes_when_cached_snapshot_is_partial(
    engine: Engine,
) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

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
    assert fsm_2024.national_value == pytest.approx(42.0)
    assert fsm_2024.local_value == pytest.approx(24.0)

    attendance_2024 = by_metric_year[("overall_attendance_pct", "2024/25")]
    assert attendance_2024.national_value is None
    assert attendance_2024.local_value is None

    with engine.connect() as connection:
        benchmark_count = connection.execute(
            text("SELECT count(*) FROM metric_benchmarks_yearly")
        ).scalar_one()

    assert benchmark_count == 2


def test_school_trends_repository_materializes_metric_benchmarks_for_requested_urns(
    engine: Engine,
) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM metric_benchmarks_yearly"))

    inserted_rows = repository.materialize_metric_benchmarks_for_urns(("920001",))

    assert inserted_rows > 0

    benchmarks = repository.get_metric_benchmark_series("920001")
    assert benchmarks is not None

    by_metric_year = {(row.metric_key, row.academic_year): row for row in benchmarks.rows}
    fsm_2024 = by_metric_year[("fsm_pct", "2024/25")]
    assert fsm_2024.national_value is not None
    assert 0.0 <= fsm_2024.national_value <= 100.0
    assert fsm_2024.local_value is not None
    assert 0.0 <= fsm_2024.local_value <= 100.0

    finance_income_2024 = by_metric_year[("finance_income_per_pupil_gbp", "2024/25")]
    assert finance_income_2024.national_value is not None
    assert finance_income_2024.local_value is not None


def test_school_trends_repository_materializes_all_metric_benchmarks(engine: Engine) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM metric_benchmarks_yearly"))

    inserted_rows = repository.materialize_all_metric_benchmarks()

    assert inserted_rows > 0

    with engine.connect() as connection:
        scopes = {
            tuple(row)
            for row in connection.execute(
                text(
                    """
                    SELECT benchmark_scope, benchmark_area
                    FROM metric_benchmarks_yearly
                    WHERE metric_key = 'fsm_pct' AND academic_year = '2024/25'
                    ORDER BY benchmark_scope, benchmark_area
                    """
                )
            ).all()
        }

    assert ("national", "england") in scopes
    assert ("phase", "Secondary") in scopes

    with engine.connect() as connection:
        finance_scopes = {
            tuple(row)
            for row in connection.execute(
                text(
                    """
                    SELECT benchmark_scope, benchmark_area
                    FROM metric_benchmarks_yearly
                    WHERE metric_key = 'finance_income_per_pupil_gbp'
                      AND academic_year = '2024/25'
                    ORDER BY benchmark_scope, benchmark_area
                    """
                )
            ).all()
        }

    assert ("national", "england") in finance_scopes
    assert ("phase", "Secondary") in finance_scopes


def test_school_trends_repository_returns_empty_rows_for_school_without_history(
    engine: Engine,
) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    demographics = repository.get_demographics_series("920002")
    attendance = repository.get_attendance_series("920002")
    behaviour = repository.get_behaviour_series("920002")
    workforce = repository.get_workforce_series("920002")
    finance = repository.get_finance_series("920002")

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

    assert finance is not None
    assert finance.urn == "920002"
    assert finance.is_applicable is False
    assert finance.rows == ()
    assert finance.latest_updated_at is None


def test_school_trends_repository_returns_none_for_unknown_school(engine: Engine) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    demographics = repository.get_demographics_series("999999")
    attendance = repository.get_attendance_series("999999")
    behaviour = repository.get_behaviour_series("999999")
    workforce = repository.get_workforce_series("999999")
    finance = repository.get_finance_series("999999")
    benchmarks = repository.get_metric_benchmark_series("999999")

    assert demographics is None
    assert attendance is None
    assert behaviour is None
    assert workforce is None
    assert finance is None
    assert benchmarks is None
