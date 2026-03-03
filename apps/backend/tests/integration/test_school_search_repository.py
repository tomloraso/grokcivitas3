from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_school_search_repository import (
    PostgresSchoolSearchRepository,
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
    reason="Postgres database unavailable for school search repository integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    engine = _build_engine(DATABASE_URL)
    _ensure_schema(engine)
    _seed_schools(engine)
    try:
        yield engine
    finally:
        _cleanup_schools(engine)
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
                CREATE INDEX IF NOT EXISTS ix_schools_location
                ON schools USING GIST (location)
                """
            )
        )


def _seed_schools(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn,
                    name,
                    phase,
                    type,
                    status,
                    postcode,
                    easting,
                    northing,
                    location,
                    capacity,
                    pupil_count,
                    open_date,
                    close_date
                ) VALUES (
                    :urn,
                    :name,
                    :phase,
                    :type,
                    :status,
                    :postcode,
                    0,
                    0,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography(Point, 4326),
                    :capacity,
                    :pupil_count,
                    :open_date,
                    NULL
                )
                ON CONFLICT (urn) DO UPDATE SET
                    name = EXCLUDED.name,
                    phase = EXCLUDED.phase,
                    type = EXCLUDED.type,
                    status = EXCLUDED.status,
                    postcode = EXCLUDED.postcode,
                    location = EXCLUDED.location,
                    capacity = EXCLUDED.capacity,
                    pupil_count = EXCLUDED.pupil_count,
                    open_date = EXCLUDED.open_date
                """
            ),
            [
                {
                    "urn": "900001",
                    "name": "Nearby Open School",
                    "phase": "Primary",
                    "type": "Community school",
                    "status": "Open",
                    "postcode": "SW1A 1AA",
                    "lat": 0.02,
                    "lng": 0.0,
                    "capacity": 250,
                    "pupil_count": 220,
                    "open_date": date(2000, 1, 1),
                },
                {
                    "urn": "900002",
                    "name": "Further Open School",
                    "phase": "Secondary",
                    "type": "Academy sponsor led",
                    "status": "Open",
                    "postcode": "W1A 1AA",
                    "lat": 0.04,
                    "lng": 0.0,
                    "capacity": 1100,
                    "pupil_count": 980,
                    "open_date": date(1995, 9, 1),
                },
                {
                    "urn": "900003",
                    "name": "Closed School",
                    "phase": "Primary",
                    "type": "Community school",
                    "status": "Closed",
                    "postcode": "SW1A 2AA",
                    "lat": 0.03,
                    "lng": 0.0,
                    "capacity": 300,
                    "pupil_count": 0,
                    "open_date": date(1990, 9, 1),
                },
                {
                    "urn": "900004",
                    "name": "Zeta Congleton High School",
                    "phase": "Secondary",
                    "type": "Academy converter",
                    "status": "Open",
                    "postcode": "CW12 4NS",
                    "lat": 53.4630,
                    "lng": -2.2400,
                    "capacity": 1000,
                    "pupil_count": 900,
                    "open_date": date(2011, 4, 1),
                },
                {
                    "urn": "900005",
                    "name": "Zeta Congleton Academy",
                    "phase": "Secondary",
                    "type": "Academy converter",
                    "status": "Open",
                    "postcode": "CW12 4AB",
                    "lat": 53.4640,
                    "lng": -2.2410,
                    "capacity": 900,
                    "pupil_count": 800,
                    "open_date": date(2012, 9, 1),
                },
                {
                    "urn": "900006",
                    "name": "Zeta Highfield School",
                    "phase": "Secondary",
                    "type": "Academy converter",
                    "status": "Open",
                    "postcode": "CW12 4AC",
                    "lat": 53.4650,
                    "lng": -2.2420,
                    "capacity": 800,
                    "pupil_count": 700,
                    "open_date": date(2013, 9, 1),
                },
                {
                    "urn": "900007",
                    "name": "Zeta Congleton High School Sixth Form",
                    "phase": "16 plus",
                    "type": "Academy converter",
                    "status": "Open",
                    "postcode": "CW12 4AD",
                    "lat": 53.4660,
                    "lng": -2.2430,
                    "capacity": 500,
                    "pupil_count": 450,
                    "open_date": date(2014, 9, 1),
                },
            ],
        )


def _cleanup_schools(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "DELETE FROM schools WHERE urn IN ('900001', '900002', '900003', '900004', '900005', '900006', '900007')"
            )
        )


def test_school_search_repository_filters_to_open_and_sorts_by_distance(engine: Engine) -> None:
    repository = PostgresSchoolSearchRepository(engine=engine)

    results = repository.search_within_radius(
        center_lat=0.0,
        center_lng=0.0,
        radius_miles=5.0,
    )

    assert [item.urn for item in results] == ["900001", "900002"]
    assert all(item.distance_miles >= 0 for item in results)
    assert results[0].distance_miles <= results[1].distance_miles
    assert results[0].lat == pytest.approx(0.02, abs=0.0005)
    assert results[0].lng == pytest.approx(0.0, abs=0.0005)


def test_school_search_repository_name_search_requires_all_tokens(engine: Engine) -> None:
    repository = PostgresSchoolSearchRepository(engine=engine)

    results = repository.search_by_name(
        name="Zeta Congleton School",
        limit=50,
    )

    assert [item.urn for item in results] == ["900004", "900007"]
    assert all(
        "Zeta" in item.name and "Congleton" in item.name and "School" in item.name
        for item in results
    )


def test_school_search_repository_name_search_prioritizes_exact_match(engine: Engine) -> None:
    repository = PostgresSchoolSearchRepository(engine=engine)

    results = repository.search_by_name(
        name="Zeta Congleton High School",
        limit=50,
    )

    assert results[0].urn == "900004"
    assert results[0].name == "Zeta Congleton High School"
