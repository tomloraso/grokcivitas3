from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_summary_context_repository import (
    PostgresSummaryContextRepository,
)


def _database_url() -> str:
    return AppSettings().database.url


def _build_engine(database_url: str, schema_name: str | None = None) -> Engine:
    if database_url.startswith("postgresql"):
        engine = create_engine(database_url, future=True, connect_args={"connect_timeout": 2})
    else:
        engine = create_engine(database_url, future=True)
    if schema_name is not None and database_url.startswith("postgresql"):

        @event.listens_for(engine, "connect")
        def _set_search_path(dbapi_connection, _connection_record) -> None:  # type: ignore[no-redef]
            with dbapi_connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema_name}"')

    return engine


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
    reason="Postgres database unavailable for summary context integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    schema_name = f"test_summary_context_{uuid4().hex}"
    admin_engine = _build_engine(DATABASE_URL)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    admin_engine.dispose()

    engine = _build_engine(DATABASE_URL, schema_name=schema_name)
    _ensure_schema(engine)
    _cleanup(engine)
    _seed(engine)
    try:
        yield engine
    finally:
        _cleanup(engine)
        engine.dispose()
        admin_engine = _build_engine(DATABASE_URL)
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        admin_engine.dispose()


def _ensure_schema(engine: Engine) -> None:
    with engine.begin() as connection:
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
                    website text NULL,
                    telephone text NULL,
                    head_title text NULL,
                    head_first_name text NULL,
                    head_last_name text NULL,
                    head_job_title text NULL,
                    statutory_low_age integer NULL,
                    statutory_high_age integer NULL,
                    gender text NULL,
                    religious_character text NULL,
                    admissions_policy text NULL,
                    sixth_form text NULL,
                    trust_name text NULL,
                    la_name text NULL,
                    urban_rural text NULL,
                    pupil_count integer NULL,
                    capacity integer NULL,
                    number_of_boys integer NULL,
                    number_of_girls integer NULL,
                    lsoa_code text NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_demographics_yearly (
                    urn text NOT NULL,
                    academic_year text NOT NULL,
                    fsm_pct double precision NULL,
                    eal_pct double precision NULL,
                    sen_pct double precision NULL,
                    ehcp_pct double precision NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_performance_yearly (
                    urn text NOT NULL,
                    academic_year text NOT NULL,
                    progress8_average double precision NULL,
                    attainment8_average double precision NULL,
                    ks2_reading_expected_pct double precision NULL,
                    ks2_maths_expected_pct double precision NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_ofsted_latest (
                    urn text PRIMARY KEY,
                    overall_effectiveness_label text NULL,
                    inspection_start_date date NULL,
                    latest_oeif_inspection_start_date date NULL,
                    latest_ungraded_inspection_date date NULL,
                    quality_of_education_label text NULL,
                    behaviour_and_attitudes_label text NULL,
                    personal_development_label text NULL,
                    leadership_and_management_label text NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ofsted_inspections (
                    urn text NOT NULL,
                    inspection_start_date date NOT NULL,
                    overall_effectiveness_label text NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS area_deprivation (
                    lsoa_code text PRIMARY KEY,
                    imd_decile integer NULL,
                    imd_rank integer NULL,
                    idaci_decile integer NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS area_crime_context (
                    urn text NOT NULL,
                    month date NOT NULL,
                    crime_category text NOT NULL,
                    incident_count integer NOT NULL,
                    radius_meters double precision NOT NULL
                )
                """
            )
        )


def _seed(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn, name, phase, type, status, postcode, website, telephone,
                    head_title, head_first_name, head_last_name, head_job_title,
                    statutory_low_age, statutory_high_age, gender, religious_character,
                    admissions_policy, sixth_form, trust_name, la_name, urban_rural,
                    pupil_count, capacity, number_of_boys, number_of_girls, lsoa_code
                ) VALUES (
                    '930001', 'Context Test School', 'Secondary', 'Academy', 'Open', 'SW1A 1AA',
                    'https://example.test', '020 7946 0999', 'Ms', 'Alex', 'Smith', 'Headteacher',
                    11, 16, 'Mixed', NULL, 'Not applicable', 'Does not have a sixth form',
                    'Example Trust', 'Westminster', 'Urban city and town', 900, 1000, 450, 450,
                    'E01004736'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_demographics_yearly (
                    urn, academic_year, fsm_pct, eal_pct, sen_pct, ehcp_pct
                ) VALUES (
                    '930001', '2022/23', 19.1, 21.8, 13.3, 3.0
                ), (
                    '930001', '2023/24', 18.7, 22.0, 13.7, 3.0
                ), (
                    '930001', '2024-25', 18.2, 22.4, 14.0, 3.1
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_performance_yearly (
                    urn, academic_year, progress8_average, attainment8_average,
                    ks2_reading_expected_pct, ks2_maths_expected_pct
                ) VALUES (
                    '930001', '2022/23', 0.12, 49.6, NULL, NULL
                ), (
                    '930001', '2023/24', 0.21, 50.5, NULL, NULL
                ), (
                    '930001', '2024-25', 0.31, 51.2, NULL, NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO school_ofsted_latest (
                    urn, overall_effectiveness_label, inspection_start_date,
                    quality_of_education_label, behaviour_and_attitudes_label,
                    personal_development_label, leadership_and_management_label
                ) VALUES (
                    '930001', 'Good', '2024-01-10', 'Good', 'Good', 'Good', 'Good'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO ofsted_inspections (
                    urn, inspection_start_date, overall_effectiveness_label
                ) VALUES (
                    '930001', '2022-01-10', 'Requires Improvement'
                ), (
                    '930001', '2024-01-10', 'Good'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO area_deprivation (lsoa_code, imd_decile, imd_rank, idaci_decile)
                VALUES ('E01004736', 7, 4825, 2)
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO area_crime_context (
                    urn, month, crime_category, incident_count, radius_meters
                ) VALUES (
                    '930001', '2025-08-01', 'violent-crime', 42, 1609.344
                ), (
                    '930001', '2025-09-01', 'violent-crime', 40, 1609.344
                ), (
                    '930001', '2025-10-01', 'anti-social-behaviour', 38, 1609.344
                ), (
                    '930001', '2025-11-01', 'violent-crime', 44, 1609.344
                ), (
                    '930001', '2025-12-01', 'anti-social-behaviour', 37, 1609.344
                ), (
                    '930001', '2026-01-01', 'violent-crime', 45, 1609.344
                )
                """
            )
        )


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM area_crime_context WHERE urn = '930001'"))
        connection.execute(text("DELETE FROM area_deprivation WHERE lsoa_code = 'E01004736'"))
        connection.execute(text("DELETE FROM ofsted_inspections WHERE urn = '930001'"))
        connection.execute(text("DELETE FROM school_ofsted_latest WHERE urn = '930001'"))
        connection.execute(text("DELETE FROM school_performance_yearly WHERE urn = '930001'"))
        connection.execute(text("DELETE FROM school_demographics_yearly WHERE urn = '930001'"))
        connection.execute(text("DELETE FROM schools WHERE urn = '930001'"))


def test_summary_context_repository_builds_overview_contexts(engine: Engine) -> None:
    repository = PostgresSummaryContextRepository(engine=engine)

    results = repository.list_overview_contexts(["930001"])

    assert len(results) == 1
    assert results[0].urn == "930001"
    assert results[0].name == "Context Test School"
    assert results[0].progress_8 == 0.31
    assert results[0].overall_effectiveness == "Good"


def test_summary_context_repository_builds_analyst_contexts(engine: Engine) -> None:
    repository = PostgresSummaryContextRepository(engine=engine)

    results = repository.list_analyst_contexts(["930001"])

    assert len(results) == 1
    assert results[0].urn == "930001"
    assert [point.year for point in results[0].progress_8_trend] == [
        "2024-25",
        "2023/24",
        "2022/23",
    ]
    assert results[0].quality_of_education == "Good"
    assert results[0].imd_rank == 4825
    assert results[0].idaci_decile == 2
    assert results[0].total_incidents_12m == 246
    assert results[0].top_crime_categories[0].category == "violent-crime"
