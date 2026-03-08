from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_school_search_repository import (
    PostgresSchoolSearchRepository,
)

SEEDED_URNS = (
    "900001",
    "900002",
    "900003",
    "900004",
    "900005",
    "900006",
    "900007",
    "900008",
    "900009",
    "900010",
    "900011",
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
    _seed_ofsted_latest(engine)
    _seed_school_performance(engine)
    try:
        yield engine
    finally:
        _cleanup_projection(engine)
        _cleanup_school_performance(engine)
        _cleanup_ofsted_latest(engine)
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
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_search_summary (
                    urn text PRIMARY KEY REFERENCES schools(urn) ON DELETE CASCADE,
                    name text NOT NULL,
                    phase text NULL,
                    type text NULL,
                    postcode text NULL,
                    location geography(Point, 4326) NOT NULL,
                    pupil_count integer NULL,
                    latest_ofsted_label text NULL,
                    latest_ofsted_sort_rank integer NULL,
                    latest_ofsted_availability text NOT NULL,
                    primary_academic_metric_key text NULL,
                    primary_academic_metric_label text NULL,
                    primary_academic_metric_value double precision NULL,
                    primary_academic_metric_availability text NOT NULL,
                    secondary_academic_metric_key text NULL,
                    secondary_academic_metric_label text NULL,
                    secondary_academic_metric_value double precision NULL,
                    secondary_academic_metric_availability text NOT NULL,
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
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_school_search_summary_location
                ON school_search_summary USING GIST (location)
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
                    "name": "Alpha Primary School",
                    "phase": "Primary",
                    "type": "Community school",
                    "status": "Open",
                    "postcode": "SW1A 1AA",
                    "lat": 0.01,
                    "lng": 0.0,
                    "capacity": 250,
                    "pupil_count": 220,
                    "open_date": date(2000, 1, 1),
                },
                {
                    "urn": "900002",
                    "name": "Beta Secondary Academy",
                    "phase": "Secondary",
                    "type": "Academy sponsor led",
                    "status": "Open",
                    "postcode": "SW1A 2AA",
                    "lat": 0.03,
                    "lng": 0.0,
                    "capacity": 1100,
                    "pupil_count": 980,
                    "open_date": date(1995, 9, 1),
                },
                {
                    "urn": "900003",
                    "name": "Gamma All-through School",
                    "phase": "All-through",
                    "type": "Academy converter",
                    "status": "Open",
                    "postcode": "SW1A 3AA",
                    "lat": 0.02,
                    "lng": 0.0,
                    "capacity": 1200,
                    "pupil_count": 830,
                    "open_date": date(2010, 9, 1),
                },
                {
                    "urn": "900004",
                    "name": "Delta Secondary College",
                    "phase": "Secondary",
                    "type": "Community school",
                    "status": "Open",
                    "postcode": "SW1A 4AA",
                    "lat": 0.015,
                    "lng": 0.0,
                    "capacity": 900,
                    "pupil_count": 700,
                    "open_date": date(2005, 9, 1),
                },
                {
                    "urn": "900005",
                    "name": "Closed School",
                    "phase": "Primary",
                    "type": "Community school",
                    "status": "Closed",
                    "postcode": "SW1A 5AA",
                    "lat": 0.04,
                    "lng": 0.0,
                    "capacity": 300,
                    "pupil_count": 0,
                    "open_date": date(1990, 9, 1),
                },
                {
                    "urn": "900006",
                    "name": "Middle Deemed Primary School",
                    "phase": "Middle deemed primary",
                    "type": "Voluntary aided school",
                    "status": "Open",
                    "postcode": "SW1A 6AA",
                    "lat": 0.025,
                    "lng": 0.0,
                    "capacity": 500,
                    "pupil_count": 410,
                    "open_date": date(1998, 9, 1),
                },
                {
                    "urn": "900007",
                    "name": "Middle Deemed Secondary School",
                    "phase": "Middle deemed secondary",
                    "type": "Foundation school",
                    "status": "Open",
                    "postcode": "SW1A 7AA",
                    "lat": 0.018,
                    "lng": 0.0,
                    "capacity": 620,
                    "pupil_count": 540,
                    "open_date": date(2002, 9, 1),
                },
                {
                    "urn": "900008",
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
                    "urn": "900009",
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
                    "urn": "900010",
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
                    "urn": "900011",
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


def _seed_ofsted_latest(engine: Engine) -> None:
    with engine.begin() as connection:
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
                    :urn,
                    :inspection_start_date,
                    :publication_date,
                    :overall_effectiveness_code,
                    :overall_effectiveness_label,
                    true,
                    NULL,
                    'https://example.test/ofsted.csv',
                    '2026-01'
                )
                ON CONFLICT (urn) DO UPDATE SET
                    inspection_start_date = EXCLUDED.inspection_start_date,
                    publication_date = EXCLUDED.publication_date,
                    overall_effectiveness_code = EXCLUDED.overall_effectiveness_code,
                    overall_effectiveness_label = EXCLUDED.overall_effectiveness_label,
                    is_graded = EXCLUDED.is_graded,
                    ungraded_outcome = EXCLUDED.ungraded_outcome,
                    source_asset_url = EXCLUDED.source_asset_url,
                    source_asset_month = EXCLUDED.source_asset_month
                """
            ),
            [
                {
                    "urn": "900001",
                    "inspection_start_date": date(2025, 10, 10),
                    "publication_date": date(2025, 11, 15),
                    "overall_effectiveness_code": "2",
                    "overall_effectiveness_label": "Good",
                },
                {
                    "urn": "900002",
                    "inspection_start_date": date(2024, 10, 10),
                    "publication_date": date(2024, 11, 15),
                    "overall_effectiveness_code": "1",
                    "overall_effectiveness_label": "Outstanding",
                },
                {
                    "urn": "900003",
                    "inspection_start_date": date(2023, 10, 10),
                    "publication_date": date(2023, 11, 15),
                    "overall_effectiveness_code": "2",
                    "overall_effectiveness_label": "Good",
                },
                {
                    "urn": "900006",
                    "inspection_start_date": date(2022, 10, 10),
                    "publication_date": date(2022, 11, 15),
                    "overall_effectiveness_code": "3",
                    "overall_effectiveness_label": "Requires improvement",
                },
                {
                    "urn": "900007",
                    "inspection_start_date": date(2021, 10, 10),
                    "publication_date": date(2021, 11, 15),
                    "overall_effectiveness_code": "4",
                    "overall_effectiveness_label": "Inadequate",
                },
            ],
        )


def _seed_school_performance(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO school_performance_yearly (
                    urn,
                    academic_year,
                    progress8_average,
                    ks2_combined_expected_pct
                ) VALUES (
                    :urn,
                    '2024/25',
                    :progress8_average,
                    :ks2_combined_expected_pct
                )
                ON CONFLICT (urn, academic_year) DO UPDATE SET
                    progress8_average = EXCLUDED.progress8_average,
                    ks2_combined_expected_pct = EXCLUDED.ks2_combined_expected_pct
                """
            ),
            [
                {
                    "urn": "900001",
                    "progress8_average": None,
                    "ks2_combined_expected_pct": 62.0,
                },
                {
                    "urn": "900002",
                    "progress8_average": 0.41,
                    "ks2_combined_expected_pct": None,
                },
                {
                    "urn": "900003",
                    "progress8_average": 0.52,
                    "ks2_combined_expected_pct": 65.0,
                },
                {
                    "urn": "900004",
                    "progress8_average": 0.12,
                    "ks2_combined_expected_pct": None,
                },
                {
                    "urn": "900007",
                    "progress8_average": -0.12,
                    "ks2_combined_expected_pct": None,
                },
            ],
        )


def _cleanup_projection(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM school_search_summary WHERE urn IN :urns").bindparams(
                urns=SEEDED_URNS, expanding=True
            )
        )


def _cleanup_school_performance(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM school_performance_yearly WHERE urn IN :urns").bindparams(
                urns=SEEDED_URNS, expanding=True
            )
        )


def _cleanup_ofsted_latest(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM school_ofsted_latest WHERE urn IN :urns").bindparams(
                urns=SEEDED_URNS, expanding=True
            )
        )


def _cleanup_schools(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM schools WHERE urn IN :urns").bindparams(
                urns=SEEDED_URNS,
                expanding=True,
            )
        )


def test_school_search_repository_materializes_search_summary_projection(engine: Engine) -> None:
    repository = PostgresSchoolSearchRepository(engine=engine)

    materialized_rows = repository.materialize_all_search_summaries()

    assert materialized_rows == 10

    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    """
                SELECT
                    latest_ofsted_label,
                    latest_ofsted_sort_rank,
                    latest_ofsted_availability,
                    primary_academic_metric_key,
                    primary_academic_metric_value,
                    primary_academic_metric_availability,
                    secondary_academic_metric_key,
                    secondary_academic_metric_value,
                    secondary_academic_metric_availability
                FROM school_search_summary
                WHERE urn = '900003'
                """
                )
            )
            .mappings()
            .one()
        )
        missing_metric_row = (
            connection.execute(
                text(
                    """
                SELECT
                    latest_ofsted_label,
                    latest_ofsted_sort_rank,
                    latest_ofsted_availability,
                    primary_academic_metric_key,
                    primary_academic_metric_value,
                    primary_academic_metric_availability
                FROM school_search_summary
                WHERE urn = '900006'
                """
                )
            )
            .mappings()
            .one()
        )

    assert row["latest_ofsted_label"] == "Good"
    assert row["latest_ofsted_sort_rank"] == 2
    assert row["latest_ofsted_availability"] == "published"
    assert row["primary_academic_metric_key"] == "ks2_combined_expected_pct"
    assert row["primary_academic_metric_value"] == pytest.approx(65.0)
    assert row["primary_academic_metric_availability"] == "published"
    assert row["secondary_academic_metric_key"] == "progress8_average"
    assert row["secondary_academic_metric_value"] == pytest.approx(0.52)
    assert row["secondary_academic_metric_availability"] == "published"

    assert missing_metric_row["latest_ofsted_label"] == "Requires improvement"
    assert missing_metric_row["latest_ofsted_sort_rank"] == 3
    assert missing_metric_row["latest_ofsted_availability"] == "published"
    assert missing_metric_row["primary_academic_metric_key"] == "ks2_combined_expected_pct"
    assert missing_metric_row["primary_academic_metric_value"] is None
    assert missing_metric_row["primary_academic_metric_availability"] == "not_published"


def test_school_search_repository_filters_to_primary_family_and_sorts_by_academic_metric(
    engine: Engine,
) -> None:
    repository = PostgresSchoolSearchRepository(engine=engine)
    repository.materialize_all_search_summaries()

    results = repository.search_within_radius(
        center_lat=0.0,
        center_lng=0.0,
        radius_miles=5.0,
        phase_filters=("primary",),
        sort="academic",
    )

    assert [item.urn for item in results] == ["900003", "900001", "900006"]
    assert [item.academic_metric.metric_key for item in results] == [
        "ks2_combined_expected_pct",
        "ks2_combined_expected_pct",
        "ks2_combined_expected_pct",
    ]
    assert [item.academic_metric.sort_value for item in results] == [65.0, 62.0, None]
    assert results[0].academic_metric.display_value == "65%"
    assert results[1].academic_metric.display_value == "62%"
    assert results[2].academic_metric.display_value is None
    assert results[2].academic_metric.availability == "not_published"
    assert results[0].phase == "All-through"


def test_school_search_repository_filters_to_secondary_family_and_sorts_by_ofsted(
    engine: Engine,
) -> None:
    repository = PostgresSchoolSearchRepository(engine=engine)
    repository.materialize_all_search_summaries()

    results = repository.search_within_radius(
        center_lat=0.0,
        center_lng=0.0,
        radius_miles=5.0,
        phase_filters=("secondary",),
        sort="ofsted",
    )

    assert [item.urn for item in results] == ["900002", "900003", "900007", "900004"]
    assert [item.latest_ofsted.sort_rank for item in results] == [1, 2, 4, None]
    assert [item.academic_metric.metric_key for item in results] == [
        "progress8_average",
        "progress8_average",
        "progress8_average",
        "progress8_average",
    ]
    assert results[0].academic_metric.display_value == "0.41"
    assert results[1].academic_metric.display_value == "0.52"
    assert results[3].latest_ofsted.availability == "not_published"


def test_school_search_repository_name_search_requires_all_tokens(engine: Engine) -> None:
    repository = PostgresSchoolSearchRepository(engine=engine)

    results = repository.search_by_name(
        name="Zeta Congleton School",
        limit=50,
    )

    assert [item.urn for item in results] == ["900008", "900011"]
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

    assert results[0].urn == "900008"
    assert results[0].name == "Zeta Congleton High School"
