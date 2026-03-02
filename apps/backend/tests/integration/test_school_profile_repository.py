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


def _cleanup_data(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM school_ofsted_latest WHERE urn = '910001'"))
        connection.execute(text("DELETE FROM school_demographics_yearly WHERE urn = '910001'"))
        connection.execute(text("DELETE FROM schools WHERE urn = '910001'"))


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


def test_school_profile_repository_returns_none_for_unknown_urn(engine: Engine) -> None:
    repository = PostgresSchoolProfileRepository(engine=engine)

    result = repository.get_school_profile("999999")

    assert result is None
