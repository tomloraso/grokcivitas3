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
                CREATE TABLE IF NOT EXISTS school_demographics_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    disadvantaged_pct double precision NULL,
                    fsm_pct double precision NULL,
                    sen_pct double precision NULL,
                    sen_support_pct double precision NULL,
                    ehcp_pct double precision NULL,
                    eal_pct double precision NULL,
                    first_language_english_pct double precision NULL,
                    first_language_unclassified_pct double precision NULL,
                    total_pupils integer NULL,
                    has_ethnicity_data boolean NOT NULL DEFAULT false,
                    has_top_languages_data boolean NOT NULL DEFAULT false,
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
                CREATE TABLE IF NOT EXISTS school_ofsted_latest (
                    urn text PRIMARY KEY REFERENCES schools(urn) ON DELETE CASCADE,
                    inspection_start_date date NULL,
                    publication_date date NULL,
                    overall_effectiveness_code text NULL,
                    overall_effectiveness_label text NULL,
                    is_graded boolean NOT NULL DEFAULT false,
                    ungraded_outcome text NULL,
                    source_asset_url text NOT NULL,
                    source_asset_month text NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
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
                    NULL,
                    14.0,
                    2.5,
                    9.0,
                    89.0,
                    1.0,
                    false,
                    false,
                    'dataset-1'
                ),
                (
                    '910001',
                    '2024/25',
                    20.5,
                    NULL,
                    13.0,
                    2.1,
                    8.4,
                    90.6,
                    1.0,
                    false,
                    false,
                    'dataset-1'
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
                    is_graded = EXCLUDED.is_graded,
                    source_asset_url = EXCLUDED.source_asset_url,
                    source_asset_month = EXCLUDED.source_asset_month
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


def _cleanup_data(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM area_crime_context WHERE urn IN ('910001', '910002')"))
        connection.execute(text("DELETE FROM area_deprivation WHERE lsoa_code = 'E01004736'"))
        connection.execute(text("DELETE FROM ofsted_inspections WHERE urn IN ('910001', '910002')"))
        connection.execute(
            text("DELETE FROM school_ofsted_latest WHERE urn IN ('910001', '910002')")
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
    assert result.demographics_latest.coverage.ethnicity_supported is False
    assert result.demographics_latest.coverage.top_languages_supported is False

    assert result.ofsted_latest is not None
    assert result.ofsted_latest.overall_effectiveness_code == "2"
    assert result.ofsted_latest.overall_effectiveness_label == "Good"
    assert result.ofsted_latest.inspection_start_date == date(2025, 10, 10)
    assert result.ofsted_latest.publication_date == date(2025, 11, 15)
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
    assert result.area_context.deprivation is not None
    assert result.area_context.deprivation.lsoa_code == "E01004736"
    assert result.area_context.deprivation.imd_decile == 3
    assert result.area_context.deprivation.idaci_decile == 2
    assert result.area_context.crime is not None
    assert result.area_context.crime.radius_miles == pytest.approx(1.0, abs=0.01)
    assert result.area_context.crime.latest_month == "2026-01"
    assert result.area_context.crime.total_incidents == 219
    assert tuple(category.category for category in result.area_context.crime.categories) == (
        "violent-crime",
        "anti-social-behaviour",
    )
    assert result.completeness.demographics.status == "partial"
    assert result.completeness.demographics.reason_code == "partial_metric_coverage"
    assert result.completeness.demographics.last_updated_at is not None
    assert result.completeness.ofsted_latest.status == "available"
    assert result.completeness.ofsted_timeline.status == "available"
    assert result.completeness.area_deprivation.status == "available"
    assert result.completeness.area_crime.status == "partial"
    assert result.completeness.area_crime.reason_code == "source_coverage_gap"


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
    assert result.area_context.crime is not None
    assert result.area_context.crime.latest_month == "2026-01"
    assert result.area_context.crime.total_incidents == 0
    assert result.area_context.crime.categories == ()
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
