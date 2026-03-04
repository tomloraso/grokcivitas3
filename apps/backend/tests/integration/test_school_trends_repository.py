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
                    sen_pct,
                    ehcp_pct,
                    eal_pct,
                    first_language_english_pct,
                    first_language_unclassified_pct,
                    source_dataset_id
                ) VALUES
                (
                    '920001',
                    '2024/25',
                    18.0,
                    12.0,
                    2.4,
                    9.1,
                    88.9,
                    0.7,
                    'dataset-1'
                ),
                (
                    '920001',
                    '2023/24',
                    19.5,
                    11.5,
                    2.3,
                    8.8,
                    89.4,
                    0.6,
                    'dataset-1'
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    disadvantaged_pct = EXCLUDED.disadvantaged_pct,
                    sen_pct = EXCLUDED.sen_pct,
                    ehcp_pct = EXCLUDED.ehcp_pct,
                    eal_pct = EXCLUDED.eal_pct,
                    first_language_english_pct = EXCLUDED.first_language_english_pct,
                    first_language_unclassified_pct = EXCLUDED.first_language_unclassified_pct
                """
            )
        )


def _cleanup_data(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM school_demographics_yearly WHERE urn IN ('920001', '920002')")
        )
        connection.execute(text("DELETE FROM schools WHERE urn IN ('920001', '920002')"))


def test_school_trends_repository_returns_demographics_ordered_by_academic_year(
    engine: Engine,
) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    result = repository.get_demographics_series("920001")

    assert result is not None
    assert result.urn == "920001"
    assert [row.academic_year for row in result.rows] == ["2023/24", "2024/25"]
    assert result.rows[0].disadvantaged_pct == 19.5
    assert result.rows[1].disadvantaged_pct == 18.0
    assert result.rows[0].first_language_english_pct == 89.4
    assert result.rows[1].first_language_unclassified_pct == 0.7
    assert result.latest_updated_at is not None


def test_school_trends_repository_returns_empty_rows_for_school_without_demographics(
    engine: Engine,
) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    result = repository.get_demographics_series("920002")

    assert result is not None
    assert result.urn == "920002"
    assert result.rows == ()
    assert result.latest_updated_at is None


def test_school_trends_repository_returns_none_for_unknown_school(engine: Engine) -> None:
    repository = PostgresSchoolTrendsRepository(engine=engine)

    result = repository.get_demographics_series("999999")

    assert result is None
