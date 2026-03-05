from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_school_profile_repository import (
    PostgresSchoolProfileRepository,
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
    reason="Postgres database unavailable for school profile repository integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    engine = _build_engine(DATABASE_URL)
    _ensure_schema(engine)
    _cleanup_data(engine)
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
                CREATE TABLE IF NOT EXISTS postcode_cache (
                    postcode text PRIMARY KEY,
                    lat double precision NOT NULL,
                    lng double precision NOT NULL,
                    lsoa_code text NULL,
                    lsoa text NULL,
                    admin_district text NULL,
                    cached_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE postcode_cache
                ADD COLUMN IF NOT EXISTS lsoa_code text NULL
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ofsted_inspections (
                    inspection_number text PRIMARY KEY,
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    inspection_start_date date NOT NULL,
                    inspection_end_date date NULL,
                    publication_date date NULL,
                    inspection_type text NULL,
                    inspection_type_grouping text NULL,
                    event_type_grouping text NULL,
                    overall_effectiveness_code text NULL,
                    overall_effectiveness_label text NULL,
                    headline_outcome_text text NULL,
                    category_of_concern text NULL,
                    source_schema_version text NOT NULL,
                    source_asset_url text NOT NULL,
                    source_asset_month text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS area_deprivation (
                    lsoa_code text PRIMARY KEY,
                    lsoa_name text NOT NULL,
                    local_authority_district_code text NULL,
                    local_authority_district_name text NULL,
                    imd_score double precision NOT NULL,
                    imd_rank integer NOT NULL,
                    imd_decile integer NOT NULL,
                    idaci_score double precision NOT NULL,
                    idaci_rank integer NOT NULL,
                    idaci_decile integer NOT NULL,
                    source_release text NOT NULL,
                    lsoa_vintage text NOT NULL,
                    source_file_url text NOT NULL,
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
                "ADD COLUMN IF NOT EXISTS income_score double precision NULL"
            )
        )
        connection.execute(
            text("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS income_rank integer NULL")
        )
        connection.execute(
            text("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS income_decile integer NULL")
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS employment_score double precision NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS employment_rank integer NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS employment_decile integer NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS education_score double precision NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS education_rank integer NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS education_decile integer NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS health_score double precision NULL"
            )
        )
        connection.execute(
            text("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS health_rank integer NULL")
        )
        connection.execute(
            text("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS health_decile integer NULL")
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS crime_score double precision NULL"
            )
        )
        connection.execute(
            text("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS crime_rank integer NULL")
        )
        connection.execute(
            text("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS crime_decile integer NULL")
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS barriers_score double precision NULL"
            )
        )
        connection.execute(
            text("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS barriers_rank integer NULL")
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS barriers_decile integer NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS living_environment_score double precision NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS living_environment_rank integer NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_deprivation "
                "ADD COLUMN IF NOT EXISTS living_environment_decile integer NULL"
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
                    has_fsm6_data boolean NOT NULL DEFAULT false,
                    has_gender_data boolean NOT NULL DEFAULT false,
                    has_mobility_data boolean NOT NULL DEFAULT false,
                    has_ethnicity_data boolean NOT NULL DEFAULT false,
                    has_top_languages_data boolean NOT NULL DEFAULT false,
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
                CREATE TABLE IF NOT EXISTS school_ethnicity_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    white_british_pct double precision NULL,
                    white_british_count integer NULL,
                    irish_pct double precision NULL,
                    irish_count integer NULL,
                    traveller_of_irish_heritage_pct double precision NULL,
                    traveller_of_irish_heritage_count integer NULL,
                    any_other_white_background_pct double precision NULL,
                    any_other_white_background_count integer NULL,
                    gypsy_roma_pct double precision NULL,
                    gypsy_roma_count integer NULL,
                    white_and_black_caribbean_pct double precision NULL,
                    white_and_black_caribbean_count integer NULL,
                    white_and_black_african_pct double precision NULL,
                    white_and_black_african_count integer NULL,
                    white_and_asian_pct double precision NULL,
                    white_and_asian_count integer NULL,
                    any_other_mixed_background_pct double precision NULL,
                    any_other_mixed_background_count integer NULL,
                    indian_pct double precision NULL,
                    indian_count integer NULL,
                    pakistani_pct double precision NULL,
                    pakistani_count integer NULL,
                    bangladeshi_pct double precision NULL,
                    bangladeshi_count integer NULL,
                    any_other_asian_background_pct double precision NULL,
                    any_other_asian_background_count integer NULL,
                    caribbean_pct double precision NULL,
                    caribbean_count integer NULL,
                    african_pct double precision NULL,
                    african_count integer NULL,
                    any_other_black_background_pct double precision NULL,
                    any_other_black_background_count integer NULL,
                    chinese_pct double precision NULL,
                    chinese_count integer NULL,
                    any_other_ethnic_group_pct double precision NULL,
                    any_other_ethnic_group_count integer NULL,
                    unclassified_pct double precision NULL,
                    unclassified_count integer NULL,
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
                CREATE TABLE IF NOT EXISTS area_house_price_context (
                    area_code text NOT NULL,
                    area_name text NOT NULL,
                    month date NOT NULL,
                    average_price double precision NOT NULL,
                    annual_change_pct double precision NULL,
                    monthly_change_pct double precision NULL,
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
                "ALTER TABLE area_house_price_context "
                "ADD COLUMN IF NOT EXISTS source_dataset_id text NOT NULL DEFAULT 'uk_hpi_average_price'"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_house_price_context "
                "ADD COLUMN IF NOT EXISTS source_dataset_version text NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE area_house_price_context "
                "ADD COLUMN IF NOT EXISTS source_file_url text NOT NULL DEFAULT ''"
            )
        )
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'area_house_price_context'
                          AND column_name = 'source_release'
                    ) THEN
                        ALTER TABLE area_house_price_context
                            ALTER COLUMN source_release DROP NOT NULL;
                        ALTER TABLE area_house_price_context
                            ALTER COLUMN source_release SET DEFAULT 'uk_hpi_average_price';
                    END IF;
                END $$;
                """
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_demographics_yearly "
                "ADD COLUMN IF NOT EXISTS fsm6_pct double precision NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_demographics_yearly "
                "ADD COLUMN IF NOT EXISTS male_pct double precision NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_demographics_yearly "
                "ADD COLUMN IF NOT EXISTS female_pct double precision NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_demographics_yearly "
                "ADD COLUMN IF NOT EXISTS pupil_mobility_pct double precision NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_demographics_yearly "
                "ADD COLUMN IF NOT EXISTS has_fsm6_data boolean NOT NULL DEFAULT false"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_demographics_yearly "
                "ADD COLUMN IF NOT EXISTS has_gender_data boolean NOT NULL DEFAULT false"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_demographics_yearly "
                "ADD COLUMN IF NOT EXISTS has_mobility_data boolean NOT NULL DEFAULT false"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE school_demographics_yearly "
                "ADD COLUMN IF NOT EXISTS has_send_primary_need_data boolean NOT NULL DEFAULT false"
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_send_primary_need_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    need_key text NOT NULL,
                    need_label text NOT NULL,
                    pupil_count integer NULL,
                    percentage double precision NULL,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year, need_key)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_home_language_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    language_key text NOT NULL,
                    language_label text NOT NULL,
                    rank integer NOT NULL,
                    pupil_count integer NULL,
                    percentage double precision NULL,
                    source_dataset_id text NOT NULL,
                    source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year, language_key)
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
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_ofsted_latest (
                    urn text PRIMARY KEY REFERENCES schools(urn) ON DELETE CASCADE,
                    inspection_start_date date NULL,
                    publication_date date NULL,
                    overall_effectiveness_code text NULL,
                    overall_effectiveness_label text NULL,
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
                    ks2_source_dataset_id text NULL,
                    ks2_source_dataset_version text NULL,
                    ks4_source_dataset_id text NULL,
                    ks4_source_dataset_version text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year)
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
                    '910001',
                    'Profile Test School',
                    'Primary',
                    'Community school',
                    'Open',
                    'SW1A 1AA',
                    0,
                    0,
                    ST_SetSRID(ST_MakePoint(-0.1416, 51.5010), 4326)::geography(Point, 4326),
                    350,
                    300,
                    '2005-09-01',
                    NULL
                ),
                (
                    '910002',
                    'Profile Zero Crime School',
                    'Primary',
                    'Community school',
                    'Open',
                    NULL,
                    0,
                    0,
                    ST_SetSRID(ST_MakePoint(-0.1600, 51.5000), 4326)::geography(Point, 4326),
                    200,
                    180,
                    '2010-09-01',
                    NULL
                )
                ON CONFLICT (urn) DO NOTHING
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO postcode_cache (
                    postcode,
                    lat,
                    lng,
                    lsoa_code,
                    lsoa,
                    admin_district
                ) VALUES (
                    'SW1A 1AA',
                    51.5010,
                    -0.1416,
                    'E01004736',
                    'This name does not match deprivation LSOA',
                    'Westminster'
                )
                ON CONFLICT (postcode) DO UPDATE SET
                    lat = EXCLUDED.lat,
                    lng = EXCLUDED.lng,
                    lsoa_code = EXCLUDED.lsoa_code,
                    lsoa = EXCLUDED.lsoa,
                    admin_district = EXCLUDED.admin_district,
                    cached_at = timezone('utc', now())
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
                    sen_pct,
                    ehcp_pct,
                    eal_pct,
                    first_language_english_pct,
                    first_language_unclassified_pct,
                    has_ethnicity_data,
                    has_top_languages_data,
                    source_dataset_id
                ) VALUES
                (
                    '910001',
                    '2023/24',
                    22.0,
                    21.4,
                    14.0,
                    2.5,
                    9.0,
                    89.0,
                    1.0,
                    false,
                    false,
                    'spc:spc-rv-2023|sen:sen-rv-2023'
                ),
                (
                    '910001',
                    '2024/25',
                    20.5,
                    20.0,
                    13.0,
                    2.1,
                    8.4,
                    90.6,
                    1.0,
                    true,
                    false,
                    'spc:spc-rv-2024|sen:sen-rv-2024'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    disadvantaged_pct = EXCLUDED.disadvantaged_pct,
                    sen_pct = EXCLUDED.sen_pct,
                    ehcp_pct = EXCLUDED.ehcp_pct,
                    eal_pct = EXCLUDED.eal_pct,
                    first_language_english_pct = EXCLUDED.first_language_english_pct,
                    first_language_unclassified_pct = EXCLUDED.first_language_unclassified_pct,
                    has_ethnicity_data = EXCLUDED.has_ethnicity_data,
                    has_top_languages_data = EXCLUDED.has_top_languages_data
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_ethnicity_yearly (
                    urn,
                    academic_year,
                    white_british_pct,
                    white_british_count,
                    indian_pct,
                    indian_count,
                    african_pct,
                    african_count,
                    unclassified_pct,
                    unclassified_count,
                    source_dataset_id
                ) VALUES (
                    '910001',
                    '2024/25',
                    49.0,
                    98,
                    7.0,
                    14,
                    6.0,
                    12,
                    4.0,
                    8,
                    'spc:spc-rv-2024'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    white_british_pct = EXCLUDED.white_british_pct,
                    white_british_count = EXCLUDED.white_british_count,
                    indian_pct = EXCLUDED.indian_pct,
                    indian_count = EXCLUDED.indian_count,
                    african_pct = EXCLUDED.african_pct,
                    african_count = EXCLUDED.african_count,
                    unclassified_pct = EXCLUDED.unclassified_pct,
                    unclassified_count = EXCLUDED.unclassified_count
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
                    source_dataset_id,
                    source_dataset_version
                ) VALUES
                (
                    '910001',
                    '2023/24',
                    92.8,
                    7.2,
                    15.3,
                    'attendance:rv-2024',
                    'attendance:file-2024'
                ),
                (
                    '910001',
                    '2024/25',
                    93.2,
                    6.8,
                    14.1,
                    'attendance:rv-2025',
                    'attendance:file-2025'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    overall_attendance_pct = EXCLUDED.overall_attendance_pct,
                    overall_absence_pct = EXCLUDED.overall_absence_pct,
                    persistent_absence_pct = EXCLUDED.persistent_absence_pct,
                    source_dataset_id = EXCLUDED.source_dataset_id,
                    source_dataset_version = EXCLUDED.source_dataset_version
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
                    source_dataset_id,
                    source_dataset_version
                ) VALUES
                (
                    '910001',
                    '2023/24',
                    109,
                    14.8,
                    1,
                    0.1,
                    'behaviour:rv-2024',
                    'behaviour:file-2024'
                ),
                (
                    '910001',
                    '2024/25',
                    121,
                    16.4,
                    1,
                    0.1,
                    'behaviour:rv-2025',
                    'behaviour:file-2025'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    suspensions_count = EXCLUDED.suspensions_count,
                    suspensions_rate = EXCLUDED.suspensions_rate,
                    permanent_exclusions_count = EXCLUDED.permanent_exclusions_count,
                    permanent_exclusions_rate = EXCLUDED.permanent_exclusions_rate,
                    source_dataset_id = EXCLUDED.source_dataset_id,
                    source_dataset_version = EXCLUDED.source_dataset_version
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
                    source_dataset_id,
                    source_dataset_version
                ) VALUES
                (
                    '910001',
                    '2023/24',
                    16.7,
                    2.8,
                    74.0,
                    10.2,
                    95.1,
                    80.3,
                    'workforce:rv-2024',
                    'workforce:file-2024'
                ),
                (
                    '910001',
                    '2024/25',
                    16.3,
                    2.4,
                    76.5,
                    9.8,
                    95.2,
                    81.1,
                    'workforce:rv-2025',
                    'workforce:file-2025'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    pupil_teacher_ratio = EXCLUDED.pupil_teacher_ratio,
                    supply_staff_pct = EXCLUDED.supply_staff_pct,
                    teachers_3plus_years_pct = EXCLUDED.teachers_3plus_years_pct,
                    teacher_turnover_pct = EXCLUDED.teacher_turnover_pct,
                    qts_pct = EXCLUDED.qts_pct,
                    qualifications_level6_plus_pct = EXCLUDED.qualifications_level6_plus_pct,
                    source_dataset_id = EXCLUDED.source_dataset_id,
                    source_dataset_version = EXCLUDED.source_dataset_version
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_leadership_snapshot (
                    urn,
                    headteacher_name,
                    headteacher_start_date,
                    headteacher_tenure_years,
                    leadership_turnover_score,
                    source_dataset_id,
                    source_dataset_version
                ) VALUES (
                    '910001',
                    'A. Jones',
                    '2020-09-01',
                    4.5,
                    1.2,
                    'workforce:rv-2025',
                    'workforce:file-2025'
                )
                ON CONFLICT (urn) DO UPDATE SET
                    headteacher_name = EXCLUDED.headteacher_name,
                    headteacher_start_date = EXCLUDED.headteacher_start_date,
                    headteacher_tenure_years = EXCLUDED.headteacher_tenure_years,
                    leadership_turnover_score = EXCLUDED.leadership_turnover_score,
                    source_dataset_id = EXCLUDED.source_dataset_id,
                    source_dataset_version = EXCLUDED.source_dataset_version
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO ofsted_inspections (
                    inspection_number,
                    urn,
                    inspection_start_date,
                    publication_date,
                    inspection_type,
                    overall_effectiveness_label,
                    headline_outcome_text,
                    category_of_concern,
                    source_schema_version,
                    source_asset_url,
                    source_asset_month
                ) VALUES
                (
                    '910001-historical',
                    '910001',
                    '2015-09-14',
                    '2015-10-10',
                    'S5 Inspection',
                    'Good',
                    NULL,
                    NULL,
                    'all_inspections_historical_2015_2019',
                    'https://assets.publishing.service.gov.uk/media/example/historical.csv',
                    '2019-08'
                ),
                (
                    '910001-latest',
                    '910001',
                    '2025-11-11',
                    '2026-01-11',
                    'S5 Inspection',
                    NULL,
                    'Strong standard',
                    NULL,
                    'all_inspections_ytd',
                    'https://assets.publishing.service.gov.uk/media/example/ytd.csv',
                    '2026-01'
                )
                ON CONFLICT (inspection_number) DO UPDATE SET
                    publication_date = EXCLUDED.publication_date,
                    inspection_type = EXCLUDED.inspection_type,
                    overall_effectiveness_label = EXCLUDED.overall_effectiveness_label,
                    headline_outcome_text = EXCLUDED.headline_outcome_text,
                    source_asset_url = EXCLUDED.source_asset_url
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_ofsted_latest (
                    urn,
                    inspection_start_date,
                    publication_date,
                    overall_effectiveness_code,
                    overall_effectiveness_label,
                    latest_oeif_inspection_start_date,
                    latest_oeif_publication_date,
                    quality_of_education_code,
                    quality_of_education_label,
                    behaviour_and_attitudes_code,
                    behaviour_and_attitudes_label,
                    personal_development_code,
                    personal_development_label,
                    leadership_and_management_code,
                    leadership_and_management_label,
                    latest_ungraded_inspection_date,
                    latest_ungraded_publication_date,
                    is_graded,
                    ungraded_outcome,
                    source_asset_url,
                    source_asset_month
                ) VALUES (
                    '910001',
                    '2025-10-10',
                    '2025-11-15',
                    '2',
                    'Good',
                    '2025-10-10',
                    '2025-11-15',
                    '2',
                    'Good',
                    '2',
                    'Good',
                    '2',
                    'Good',
                    '2',
                    'Good',
                    '2026-01-02',
                    '2026-01-20',
                    true,
                    NULL,
                    'https://assets.publishing.service.gov.uk/media/example/latest.csv',
                    '2026-01'
                )
                ON CONFLICT (urn) DO UPDATE SET
                    overall_effectiveness_code = EXCLUDED.overall_effectiveness_code,
                    overall_effectiveness_label = EXCLUDED.overall_effectiveness_label,
                    inspection_start_date = EXCLUDED.inspection_start_date,
                    publication_date = EXCLUDED.publication_date,
                    latest_oeif_inspection_start_date = EXCLUDED.latest_oeif_inspection_start_date,
                    latest_oeif_publication_date = EXCLUDED.latest_oeif_publication_date,
                    quality_of_education_code = EXCLUDED.quality_of_education_code,
                    quality_of_education_label = EXCLUDED.quality_of_education_label,
                    behaviour_and_attitudes_code = EXCLUDED.behaviour_and_attitudes_code,
                    behaviour_and_attitudes_label = EXCLUDED.behaviour_and_attitudes_label,
                    personal_development_code = EXCLUDED.personal_development_code,
                    personal_development_label = EXCLUDED.personal_development_label,
                    leadership_and_management_code = EXCLUDED.leadership_and_management_code,
                    leadership_and_management_label = EXCLUDED.leadership_and_management_label,
                    latest_ungraded_inspection_date = EXCLUDED.latest_ungraded_inspection_date,
                    latest_ungraded_publication_date = EXCLUDED.latest_ungraded_publication_date,
                    is_graded = EXCLUDED.is_graded,
                    source_asset_url = EXCLUDED.source_asset_url,
                    source_asset_month = EXCLUDED.source_asset_month
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
                    progress8_disadvantaged,
                    progress8_not_disadvantaged,
                    progress8_disadvantaged_gap,
                    engmath_5_plus_pct,
                    engmath_4_plus_pct,
                    ebacc_entry_pct,
                    ebacc_5_plus_pct,
                    ebacc_4_plus_pct,
                    ks2_source_dataset_id,
                    ks2_source_dataset_version,
                    ks4_source_dataset_id,
                    ks4_source_dataset_version
                )
                VALUES
                (
                    '910001',
                    '2023/24',
                    46.1,
                    0.05,
                    -0.19,
                    0.16,
                    -0.35,
                    50.1,
                    69.8,
                    35.0,
                    24.2,
                    30.1,
                    NULL,
                    NULL,
                    'ks4-v1',
                    '1'
                ),
                (
                    '910001',
                    '2024/25',
                    47.2,
                    0.11,
                    -0.12,
                    0.21,
                    -0.33,
                    52.3,
                    71.4,
                    36.2,
                    25.5,
                    31.3,
                    NULL,
                    NULL,
                    'ks4-v1',
                    '1'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    attainment8_average = EXCLUDED.attainment8_average,
                    progress8_average = EXCLUDED.progress8_average,
                    progress8_disadvantaged = EXCLUDED.progress8_disadvantaged,
                    progress8_not_disadvantaged = EXCLUDED.progress8_not_disadvantaged,
                    progress8_disadvantaged_gap = EXCLUDED.progress8_disadvantaged_gap,
                    engmath_5_plus_pct = EXCLUDED.engmath_5_plus_pct,
                    engmath_4_plus_pct = EXCLUDED.engmath_4_plus_pct,
                    ebacc_entry_pct = EXCLUDED.ebacc_entry_pct,
                    ebacc_5_plus_pct = EXCLUDED.ebacc_5_plus_pct,
                    ebacc_4_plus_pct = EXCLUDED.ebacc_4_plus_pct,
                    ks2_source_dataset_id = EXCLUDED.ks2_source_dataset_id,
                    ks2_source_dataset_version = EXCLUDED.ks2_source_dataset_version,
                    ks4_source_dataset_id = EXCLUDED.ks4_source_dataset_id,
                    ks4_source_dataset_version = EXCLUDED.ks4_source_dataset_version
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO area_deprivation (
                    lsoa_code,
                    lsoa_name,
                    local_authority_district_code,
                    local_authority_district_name,
                    imd_score,
                    imd_rank,
                    imd_decile,
                    idaci_score,
                    idaci_rank,
                    idaci_decile,
                    income_score,
                    income_rank,
                    income_decile,
                    employment_score,
                    employment_rank,
                    employment_decile,
                    education_score,
                    education_rank,
                    education_decile,
                    health_score,
                    health_rank,
                    health_decile,
                    crime_score,
                    crime_rank,
                    crime_decile,
                    barriers_score,
                    barriers_rank,
                    barriers_decile,
                    living_environment_score,
                    living_environment_rank,
                    living_environment_decile,
                    population_total,
                    source_release,
                    lsoa_vintage,
                    source_file_url
                ) VALUES (
                    'E01004736',
                    'Westminster 018C',
                    'E09000033',
                    'Westminster',
                    22.4,
                    10234,
                    3,
                    0.241,
                    7284,
                    2,
                    0.125,
                    9500,
                    3,
                    0.102,
                    8800,
                    3,
                    0.154,
                    10400,
                    4,
                    0.118,
                    9200,
                    3,
                    0.176,
                    11050,
                    4,
                    0.129,
                    9850,
                    3,
                    0.171,
                    10920,
                    4,
                    2000,
                    'IoD2025',
                    '2021',
                    'https://assets.publishing.service.gov.uk/media/example/file_7.csv'
                )
                ON CONFLICT (lsoa_code) DO UPDATE SET
                    lsoa_name = EXCLUDED.lsoa_name,
                    imd_decile = EXCLUDED.imd_decile,
                    idaci_score = EXCLUDED.idaci_score,
                    idaci_decile = EXCLUDED.idaci_decile,
                    source_release = EXCLUDED.source_release
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO area_house_price_context (
                    area_code,
                    area_name,
                    month,
                    average_price,
                    annual_change_pct,
                    monthly_change_pct,
                    source_dataset_id,
                    source_dataset_version,
                    source_file_url
                )
                VALUES
                (
                    'E09000033',
                    'Westminster',
                    '2025-11-01',
                    800000.0,
                    5.4,
                    0.7,
                    'uk_hpi_average_price',
                    '2025-11',
                    'https://example.com/ukhpi.csv'
                ),
                (
                    'E09000033',
                    'Westminster',
                    '2025-12-01',
                    805000.0,
                    5.7,
                    0.6,
                    'uk_hpi_average_price',
                    '2025-12',
                    'https://example.com/ukhpi.csv'
                ),
                (
                    'E09000033',
                    'Westminster',
                    '2026-01-01',
                    810000.0,
                    6.0,
                    0.5,
                    'uk_hpi_average_price',
                    '2026-01',
                    'https://example.com/ukhpi.csv'
                )
                ON CONFLICT (area_code, month) DO UPDATE SET
                    average_price = EXCLUDED.average_price,
                    annual_change_pct = EXCLUDED.annual_change_pct,
                    monthly_change_pct = EXCLUDED.monthly_change_pct,
                    source_dataset_id = EXCLUDED.source_dataset_id,
                    source_dataset_version = EXCLUDED.source_dataset_version,
                    source_file_url = EXCLUDED.source_file_url
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO area_crime_context (
                    urn,
                    month,
                    crime_category,
                    incident_count,
                    radius_meters,
                    source_month
                ) VALUES
                (
                    '910001',
                    '2026-01-01',
                    'violent-crime',
                    132,
                    1609.344,
                    '2026-01'
                ),
                (
                    '910001',
                    '2026-01-01',
                    'anti-social-behaviour',
                    87,
                    1609.344,
                    '2026-01'
                ),
                (
                    '910001',
                    '2025-12-01',
                    'violent-crime',
                    101,
                    1609.344,
                    '2025-12'
                )
                ON CONFLICT (urn, month, crime_category, radius_meters) DO UPDATE SET
                    incident_count = EXCLUDED.incident_count,
                    source_month = EXCLUDED.source_month
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO area_crime_global_metadata (
                    id,
                    months_available,
                    latest_updated_at,
                    latest_month,
                    latest_radius_meters,
                    refreshed_at
                )
                SELECT
                    1,
                    COUNT(DISTINCT month)::integer,
                    MAX(updated_at),
                    MAX(month),
                    (
                        SELECT radius_meters
                        FROM area_crime_context
                        ORDER BY month DESC, updated_at DESC, radius_meters DESC
                        LIMIT 1
                    ),
                    timezone('utc', now())
                FROM area_crime_context
                ON CONFLICT (id) DO UPDATE SET
                    months_available = EXCLUDED.months_available,
                    latest_updated_at = EXCLUDED.latest_updated_at,
                    latest_month = EXCLUDED.latest_month,
                    latest_radius_meters = EXCLUDED.latest_radius_meters,
                    refreshed_at = timezone('utc', now())
                """
            )
        )


def _cleanup_data(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM area_crime_context WHERE urn IN ('910001', '910002')"))
        connection.execute(
            text("DELETE FROM area_house_price_context WHERE area_code = 'E09000033'")
        )
        connection.execute(text("DELETE FROM area_deprivation WHERE lsoa_code = 'E01004736'"))
        connection.execute(text("DELETE FROM ofsted_inspections WHERE urn IN ('910001', '910002')"))
        connection.execute(
            text("DELETE FROM school_behaviour_yearly WHERE urn IN ('910001', '910002')")
        )
        connection.execute(
            text("DELETE FROM school_leadership_snapshot WHERE urn IN ('910001', '910002')")
        )
        connection.execute(
            text("DELETE FROM school_workforce_yearly WHERE urn IN ('910001', '910002')")
        )
        connection.execute(
            text("DELETE FROM school_attendance_yearly WHERE urn IN ('910001', '910002')")
        )
        connection.execute(
            text("DELETE FROM school_performance_yearly WHERE urn IN ('910001', '910002')")
        )
        connection.execute(
            text("DELETE FROM school_ofsted_latest WHERE urn IN ('910001', '910002')")
        )
        connection.execute(
            text("DELETE FROM school_ethnicity_yearly WHERE urn IN ('910001', '910002')")
        )
        connection.execute(
            text("DELETE FROM school_home_language_yearly WHERE urn IN ('910001', '910002')")
        )
        connection.execute(
            text("DELETE FROM school_send_primary_need_yearly WHERE urn IN ('910001', '910002')")
        )
        connection.execute(
            text("DELETE FROM school_demographics_yearly WHERE urn IN ('910001', '910002')")
        )
        connection.execute(text("DELETE FROM postcode_cache WHERE postcode = 'SW1A 1AA'"))
        connection.execute(text("DELETE FROM schools WHERE urn IN ('910001', '910002')"))


def test_school_profile_repository_returns_profile_with_latest_demographics(engine: Engine) -> None:
    repository = PostgresSchoolProfileRepository(engine=engine)

    result = repository.get_school_profile("910001")

    assert result is not None
    assert result.school.urn == "910001"
    assert result.school.name == "Profile Test School"
    assert result.school.lat == pytest.approx(51.5010, abs=0.0005)
    assert result.school.lng == pytest.approx(-0.1416, abs=0.0005)

    assert result.demographics_latest is not None
    assert result.demographics_latest.academic_year == "2024/25"
    assert result.demographics_latest.disadvantaged_pct == 20.5
    assert result.demographics_latest.fsm_pct == 20.0
    assert result.demographics_latest.coverage.fsm_supported is True
    assert result.demographics_latest.coverage.ethnicity_supported is True
    assert result.demographics_latest.coverage.top_languages_supported is False
    assert len(result.demographics_latest.ethnicity_breakdown) == 4
    assert result.demographics_latest.ethnicity_breakdown[0].key == "white_british"
    assert result.demographics_latest.ethnicity_breakdown[0].percentage == 49.0
    assert result.demographics_latest.ethnicity_breakdown[0].count == 98
    assert result.attendance_latest is not None
    assert result.attendance_latest.academic_year == "2024/25"
    assert result.attendance_latest.overall_attendance_pct == 93.2
    assert result.attendance_latest.overall_absence_pct == 6.8
    assert result.attendance_latest.persistent_absence_pct == 14.1
    assert result.behaviour_latest is not None
    assert result.behaviour_latest.academic_year == "2024/25"
    assert result.behaviour_latest.suspensions_count == 121
    assert result.behaviour_latest.suspensions_rate == 16.4
    assert result.behaviour_latest.permanent_exclusions_count == 1
    assert result.behaviour_latest.permanent_exclusions_rate == 0.1
    assert result.workforce_latest is not None
    assert result.workforce_latest.academic_year == "2024/25"
    assert result.workforce_latest.pupil_teacher_ratio == 16.3
    assert result.workforce_latest.supply_staff_pct == 2.4
    assert result.workforce_latest.teachers_3plus_years_pct == 76.5
    assert result.workforce_latest.teacher_turnover_pct == 9.8
    assert result.workforce_latest.qts_pct == 95.2
    assert result.workforce_latest.qualifications_level6_plus_pct == 81.1
    assert result.leadership_snapshot is not None
    assert result.leadership_snapshot.headteacher_name == "A. Jones"
    assert result.leadership_snapshot.headteacher_start_date == date(2020, 9, 1)
    assert result.leadership_snapshot.headteacher_tenure_years == pytest.approx(4.5)
    assert result.leadership_snapshot.leadership_turnover_score == pytest.approx(1.2)

    assert result.ofsted_latest is not None
    assert result.ofsted_latest.overall_effectiveness_code == "2"
    assert result.ofsted_latest.overall_effectiveness_label == "Good"
    assert result.ofsted_latest.inspection_start_date == date(2025, 10, 10)
    assert result.ofsted_latest.publication_date == date(2025, 11, 15)
    assert result.ofsted_latest.latest_oeif_inspection_start_date == date(2025, 10, 10)
    assert result.ofsted_latest.latest_oeif_publication_date == date(2025, 11, 15)
    assert result.ofsted_latest.quality_of_education_code == "2"
    assert result.ofsted_latest.quality_of_education_label == "Good"
    assert result.ofsted_latest.behaviour_and_attitudes_code == "2"
    assert result.ofsted_latest.behaviour_and_attitudes_label == "Good"
    assert result.ofsted_latest.personal_development_code == "2"
    assert result.ofsted_latest.personal_development_label == "Good"
    assert result.ofsted_latest.leadership_and_management_code == "2"
    assert result.ofsted_latest.leadership_and_management_label == "Good"
    assert result.ofsted_latest.latest_ungraded_inspection_date == date(2026, 1, 2)
    assert result.ofsted_latest.latest_ungraded_publication_date == date(2026, 1, 20)
    assert result.ofsted_latest.most_recent_inspection_date == date(2026, 1, 2)
    assert result.ofsted_latest.days_since_most_recent_inspection is not None
    assert result.ofsted_latest.days_since_most_recent_inspection >= 0
    assert result.ofsted_timeline is not None
    assert result.ofsted_timeline.coverage.is_partial_history is False
    assert result.ofsted_timeline.coverage.earliest_event_date == date(2015, 9, 14)
    assert result.ofsted_timeline.coverage.latest_event_date == date(2025, 11, 11)
    assert result.ofsted_timeline.coverage.events_count == 2
    assert [event.inspection_number for event in result.ofsted_timeline.events] == [
        "910001-latest",
        "910001-historical",
    ]
    assert result.area_context is not None
    assert result.area_context.coverage.has_deprivation is True
    assert result.area_context.coverage.has_crime is True
    assert result.area_context.coverage.crime_months_available == 2
    assert result.area_context.coverage.has_house_prices is True
    assert result.area_context.coverage.house_price_months_available == 3
    assert result.area_context.deprivation is not None
    assert result.area_context.deprivation.lsoa_code == "E01004736"
    assert result.area_context.deprivation.imd_score == 22.4
    assert result.area_context.deprivation.imd_rank == 10234
    assert result.area_context.deprivation.imd_decile == 3
    assert result.area_context.deprivation.idaci_decile == 2
    assert result.area_context.deprivation.population_total == 2000
    assert result.area_context.crime is not None
    assert result.area_context.crime.radius_miles == pytest.approx(1.0, abs=0.01)
    assert result.area_context.crime.latest_month == "2026-01"
    assert result.area_context.crime.total_incidents == 219
    assert result.area_context.crime.population_denominator == 2000
    assert result.area_context.crime.incidents_per_1000 == pytest.approx(109.5)
    assert tuple(rate.year for rate in result.area_context.crime.annual_incidents_per_1000) == (
        2025,
        2026,
    )
    assert tuple(category.category for category in result.area_context.crime.categories) == (
        "violent-crime",
        "anti-social-behaviour",
    )
    assert result.area_context.house_prices is not None
    assert result.area_context.house_prices.area_code == "E09000033"
    assert result.area_context.house_prices.latest_month == "2026-01"
    assert result.area_context.house_prices.average_price == pytest.approx(810000.0)
    assert result.area_context.house_prices.annual_change_pct == pytest.approx(6.0)
    assert result.area_context.house_prices.monthly_change_pct == pytest.approx(0.5)
    assert result.area_context.house_prices.three_year_change_pct is None
    assert tuple(point.month for point in result.area_context.house_prices.trend) == (
        "2025-11",
        "2025-12",
        "2026-01",
    )
    assert result.completeness.demographics.status == "partial"
    assert result.completeness.demographics.reason_code == "partial_metric_coverage"
    assert result.completeness.demographics.last_updated_at is not None
    assert result.completeness.attendance.status == "available"
    assert result.completeness.attendance.reason_code is None
    assert result.completeness.behaviour.status == "available"
    assert result.completeness.behaviour.reason_code is None
    assert result.completeness.workforce.status == "available"
    assert result.completeness.workforce.reason_code is None
    assert result.completeness.leadership.status == "available"
    assert result.completeness.leadership.reason_code is None
    assert result.completeness.ofsted_latest.status == "available"
    assert result.completeness.ofsted_timeline.status == "available"
    assert result.completeness.area_deprivation.status == "available"
    assert result.completeness.area_crime.status == "partial"
    assert result.completeness.area_crime.reason_code == "source_coverage_gap"
    assert result.completeness.area_house_prices.status == "partial"
    assert result.completeness.area_house_prices.reason_code == "insufficient_years_published"


def test_school_profile_repository_returns_none_for_unknown_urn(engine: Engine) -> None:
    repository = PostgresSchoolProfileRepository(engine=engine)

    result = repository.get_school_profile("999999")

    assert result is None


def test_school_profile_repository_infers_zero_incident_crime_snapshot(engine: Engine) -> None:
    repository = PostgresSchoolProfileRepository(engine=engine)

    result = repository.get_school_profile("910002")

    assert result is not None
    assert result.school.urn == "910002"
    assert result.area_context.coverage.has_crime is True
    assert result.area_context.coverage.crime_months_available >= 1
    assert result.area_context.coverage.has_house_prices is False
    assert result.area_context.coverage.house_price_months_available == 0
    assert result.area_context.crime is not None
    assert result.area_context.crime.latest_month == "2026-01"
    assert result.area_context.crime.total_incidents == 0
    assert result.area_context.crime.categories == ()
    assert result.completeness.area_house_prices.status == "unavailable"
    assert result.completeness.area_house_prices.reason_code == "not_applicable"
    if result.area_context.coverage.crime_months_available < 12:
        assert result.completeness.area_crime.status == "partial"
        assert result.completeness.area_crime.reason_code == "source_coverage_gap"
    else:
        assert result.completeness.area_crime.status == "available"
        assert result.completeness.area_crime.reason_code == "no_incidents_in_radius"


def test_school_profile_repository_marks_area_crime_stale_after_school_refresh(
    engine: Engine,
) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE schools
                SET updated_at = timezone('utc', now()) + interval '3 days'
                WHERE urn = '910002'
                """
            )
        )

    repository = PostgresSchoolProfileRepository(engine=engine)
    result = repository.get_school_profile("910002")

    assert result is not None
    assert result.area_context.coverage.has_crime is False
    assert result.area_context.crime is None
    assert result.completeness.area_crime.status == "unavailable"
    assert result.completeness.area_crime.reason_code == "stale_after_school_refresh"
    assert result.completeness.area_crime.last_updated_at is not None
    assert result.completeness.area_house_prices.status == "unavailable"
    assert result.completeness.area_house_prices.reason_code == "not_applicable"
