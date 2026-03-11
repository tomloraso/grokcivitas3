from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.pipelines.base import PipelineRunContext, PipelineSource
from civitas.infrastructure.pipelines.school_admissions import (
    BRONZE_FILE_NAME,
    BRONZE_MANIFEST_FILE_NAME,
    SchoolAdmissionsPipeline,
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
    reason="Postgres database unavailable for school admissions pipeline integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    engine = _build_engine(DATABASE_URL)
    _ensure_schema(engine)
    try:
        yield engine
    finally:
        _cleanup(engine)
        engine.dispose()


def _ensure_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id uuid PRIMARY KEY,
                    source text NOT NULL,
                    status text NOT NULL,
                    started_at timestamptz NOT NULL,
                    finished_at timestamptz NULL,
                    bronze_path text NOT NULL,
                    downloaded_rows integer NOT NULL DEFAULT 0,
                    staged_rows integer NOT NULL DEFAULT 0,
                    promoted_rows integer NOT NULL DEFAULT 0,
                    rejected_rows integer NOT NULL DEFAULT 0,
                    error_message text NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pipeline_rejections (
                    id bigserial PRIMARY KEY,
                    run_id uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
                    source text NOT NULL,
                    stage text NOT NULL,
                    reason_code text NOT NULL,
                    raw_record jsonb NULL,
                    created_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schools (
                    urn text PRIMARY KEY,
                    establishment_number text NULL,
                    school_laestab text NULL,
                    name text NOT NULL,
                    phase text NULL,
                    type text NULL,
                    status text NULL,
                    postcode text NULL,
                    easting double precision NOT NULL,
                    northing double precision NOT NULL,
                    location geography(Point, 4326) NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS school_admissions_yearly (
                    urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
                    academic_year text NOT NULL,
                    entry_year text NULL,
                    school_laestab text NULL,
                    school_phase text NULL,
                    school_name text NOT NULL,
                    places_offered_total integer NULL,
                    preferred_offers_total integer NULL,
                    first_preference_offers integer NULL,
                    second_preference_offers integer NULL,
                    third_preference_offers integer NULL,
                    applications_any_preference integer NULL,
                    applications_first_preference integer NULL,
                    applications_second_preference integer NULL,
                    applications_third_preference integer NULL,
                    first_preference_application_to_offer_ratio double precision NULL,
                    first_preference_application_to_total_places_ratio double precision NULL,
                    cross_la_applications integer NULL,
                    cross_la_offers integer NULL,
                    admissions_policy text NULL,
                    establishment_type text NULL,
                    denomination text NULL,
                    fsm_eligible_pct double precision NULL,
                    urban_rural text NULL,
                    allthrough_school boolean NULL,
                    oversubscription_ratio double precision NULL,
                    first_preference_offer_rate double precision NULL,
                    any_preference_offer_rate double precision NULL,
                    source_file_url text NOT NULL,
                    source_updated_at_utc timestamptz NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
                    PRIMARY KEY (urn, academic_year)
                )
                """
            )
        )


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM school_admissions_yearly
                WHERE urn IN ('100001', '100002', '100003', '200001', '200002')
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM schools
                WHERE urn IN ('100001', '100002', '100003', '200001', '200002')
                """
            )
        )
        connection.execute(
            text("DELETE FROM pipeline_rejections WHERE source = 'school_admissions'")
        )


def _seed_schools(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn,
                    establishment_number,
                    school_laestab,
                    name,
                    phase,
                    type,
                    status,
                    postcode,
                    easting,
                    northing,
                    location,
                    updated_at
                ) VALUES
                (
                    '100001', '6007', '2136007', 'Alpha Primary School', 'Primary',
                    'Community school', 'Open', 'SW1A 1AA', 529090, 179645,
                    ST_GeogFromText('SRID=4326;POINT(-0.141 51.501)'), timezone('utc', now())
                ),
                (
                    '100002', '3614', '2013614', 'Beta Secondary School', 'Secondary',
                    'Academy converter', 'Open', 'EC1A 1BB', 531120, 181500,
                    ST_GeogFromText('SRID=4326;POINT(-0.102 51.521)'), timezone('utc', now())
                ),
                (
                    '100003', '7001', '7777001', 'Gamma All-through School', 'All-through',
                    'Academy sponsor led', 'Open', 'N1 1AA', 531000, 184000,
                    ST_GeogFromText('SRID=4326;POINT(-0.100 51.545)'), timezone('utc', now())
                ),
                (
                    '200001', '5001', '5555001', 'Ambiguous One', 'Primary',
                    'Community school', 'Open', 'E1 1AA', 532000, 182000,
                    ST_GeogFromText('SRID=4326;POINT(-0.080 51.530)'), timezone('utc', now())
                ),
                (
                    '200002', '5002', '5555001', 'Ambiguous Two', 'Primary',
                    'Community school', 'Open', 'E1 1AB', 532050, 182050,
                    ST_GeogFromText('SRID=4326;POINT(-0.079 51.531)'), timezone('utc', now())
                )
                ON CONFLICT (urn) DO NOTHING
                """
            )
        )


def _insert_run_row(engine: Engine, context: PipelineRunContext) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO pipeline_runs (
                    run_id,
                    source,
                    status,
                    started_at,
                    bronze_path,
                    downloaded_rows,
                    staged_rows,
                    promoted_rows,
                    rejected_rows
                ) VALUES (
                    :run_id,
                    :source,
                    'running',
                    :started_at,
                    :bronze_path,
                    0,
                    0,
                    0,
                    0
                )
                ON CONFLICT (run_id) DO NOTHING
                """
            ),
            {
                "run_id": str(context.run_id),
                "source": context.source.value,
                "started_at": context.started_at,
                "bronze_path": str(context.bronze_source_path),
            },
        )


def _context(bronze_root: Path) -> PipelineRunContext:
    return PipelineRunContext(
        run_id=uuid4(),
        source=PipelineSource.SCHOOL_ADMISSIONS,
        started_at=datetime(2026, 3, 10, 19, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _write_bronze_files(context: PipelineRunContext) -> None:
    context.bronze_source_path.mkdir(parents=True, exist_ok=True)
    admissions_csv = """time_period,time_identifier,geographic_level,country_code,country_name,region_code,region_name,old_la_code,new_la_code,la_name,school_phase,school_laestab_as_used,number_preferences_la,school_name,total_number_places_offered,number_preferred_offers,number_1st_preference_offers,number_2nd_preference_offers,number_3rd_preference_offers,times_put_as_any_preferred_school,times_put_as_1st_preference,times_put_as_2nd_preference,times_put_as_3rd_preference,proportion_1stprefs_v_1stprefoffers,proportion_1stprefs_v_totaloffers,all_applications_from_another_LA,offers_to_applicants_from_another_LA,establishment_type,denomination,FSM_eligible_percent,admissions_policy,urban_rural,allthrough_school,parliamentary_constituency_code,parliamentary_constituency_name,school_urn,entry_year
202526,Academic year,School,E92000001,England,E12000007,London,213,E09000033,Westminster,Primary,2136007,6,Alpha Primary School,60,57,49,6,2,95,72,15,8,1.4694,1.2000,33,18,Community school,None,18.5,Comprehensive,Urban major conurbation,No,E14000639,Westminster,100001,R
202526,Academic year,School,E92000001,England,E12000007,London,201,E09000001,City of London,Secondary,2013614,6,Beta Secondary School,120,115,100,10,5,180,140,25,15,1.4000,1.1667,12,7,Academy converter,None,22.0,Selective,Urban city and town,No,E14000640,City of London,,7
202526,Academic year,School,E92000001,England,E12000007,London,777,E09000999,Gamma,Primary,7777001,6,Gamma All-through School,30,25,20,3,2,50,40,5,5,2.0000,1.3333,10,5,Academy sponsor led,None,14.0,Comprehensive,Urban major conurbation,Yes,E14000641,Gamma,100003,R
202526,Academic year,School,E92000001,England,E12000007,London,777,E09000999,Gamma,Secondary,7777001,6,Gamma All-through School,120,110,100,6,4,200,150,30,20,1.5000,1.2500,50,20,Academy sponsor led,None,14.0,Comprehensive,Urban major conurbation,Yes,E14000641,Gamma,100003,7
202526,Academic year,School,E92000001,England,E12000007,London,999,E09000998,Conflict,Primary,9999999,6,Conflict School,30,30,30,0,0,40,35,3,2,1.1667,1.1667,5,3,Community school,None,11.0,Comprehensive,Urban major conurbation,No,E14000642,Conflict,100001,R
202526,Academic year,School,E92000001,England,E12000007,London,555,E09000997,Ambiguous,Primary,5555001,6,Ambiguous School,40,38,35,2,1,60,50,6,4,1.4286,1.2500,8,4,Community school,None,10.0,Comprehensive,Urban major conurbation,No,E14000643,Ambiguous,,R
202526,Academic year,School,E92000001,England,E12000007,London,213,E09000033,Westminster,Primary,2136007,6,Invalid URN School,60,57,49,6,2,95,72,15,8,1.4694,1.2000,33,18,Community school,None,18.5,Comprehensive,Urban major conurbation,No,E14000639,Westminster,ABC123,R
"""
    (context.bronze_source_path / BRONZE_FILE_NAME).write_text(admissions_csv, encoding="utf-8")
    (context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME).write_text(
        json.dumps(
            {
                "normalization_contract_version": "school_admissions.v1",
                "assets": [
                    {
                        "source_reference": "https://example.com/school_admissions.csv",
                        "bronze_file_name": BRONZE_FILE_NAME,
                        "downloaded_at": "2026-03-10T19:00:00+00:00",
                        "sha256": "sha-admissions",
                        "row_count": 7,
                        "release_version_id": "release-1",
                        "file_id": "file-1",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_school_admissions_pipeline_stage_and_promote_are_idempotent(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    _seed_schools(engine)
    pipeline = SchoolAdmissionsPipeline(engine=engine)

    first_context = _context(bronze_root)
    _write_bronze_files(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 6
    assert first_stage.rejected_rows == 1

    first_promoted = pipeline.promote(first_context)
    assert first_promoted == 3

    with engine.connect() as connection:
        admissions_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_admissions_yearly
                WHERE urn IN ('100001', '100002', '100003')
                """
            )
        ).scalar_one()
        assert admissions_rows == 3

        alpha = (
            connection.execute(
                text(
                    """
                    SELECT
                        entry_year,
                        places_offered_total,
                        applications_any_preference,
                        oversubscription_ratio,
                        first_preference_offer_rate,
                        any_preference_offer_rate
                    FROM school_admissions_yearly
                    WHERE urn = '100001' AND academic_year = '2025/26'
                    """
                )
            )
            .mappings()
            .one()
        )
        assert alpha["entry_year"] == "R"
        assert alpha["places_offered_total"] == 60
        assert alpha["applications_any_preference"] == 95
        assert alpha["oversubscription_ratio"] == pytest.approx(95.0 / 60.0)
        assert alpha["first_preference_offer_rate"] == pytest.approx(49.0 / 72.0)
        assert alpha["any_preference_offer_rate"] == pytest.approx(57.0 / 95.0)

        gamma = (
            connection.execute(
                text(
                    """
                    SELECT
                        entry_year,
                        places_offered_total,
                        preferred_offers_total,
                        first_preference_offers,
                        applications_any_preference,
                        applications_first_preference,
                        first_preference_application_to_offer_ratio,
                        first_preference_application_to_total_places_ratio,
                        oversubscription_ratio,
                        first_preference_offer_rate,
                        any_preference_offer_rate,
                        allthrough_school
                    FROM school_admissions_yearly
                    WHERE urn = '100003' AND academic_year = '2025/26'
                    """
                )
            )
            .mappings()
            .one()
        )
        assert gamma["entry_year"] is None
        assert gamma["places_offered_total"] == 150
        assert gamma["preferred_offers_total"] == 135
        assert gamma["first_preference_offers"] == 120
        assert gamma["applications_any_preference"] == 250
        assert gamma["applications_first_preference"] == 190
        assert gamma["first_preference_application_to_offer_ratio"] is None
        assert gamma["first_preference_application_to_total_places_ratio"] is None
        assert gamma["oversubscription_ratio"] == pytest.approx(250.0 / 150.0)
        assert gamma["first_preference_offer_rate"] == pytest.approx(120.0 / 190.0)
        assert gamma["any_preference_offer_rate"] == pytest.approx(135.0 / 250.0)
        assert gamma["allthrough_school"] is True

        rejection_codes = {
            (row["stage"], row["reason_code"])
            for row in connection.execute(
                text(
                    """
                    SELECT stage, reason_code
                    FROM pipeline_rejections
                    WHERE source = 'school_admissions' AND run_id = :run_id
                    """
                ),
                {"run_id": str(first_context.run_id)},
            ).mappings()
        }
        assert rejection_codes == {
            ("stage", "invalid_school_urn"),
            ("promote", "join_key_conflict"),
            ("promote", "ambiguous_school_laestab"),
        }

    second_context = _context(bronze_root)
    _insert_run_row(engine, second_context)
    second_stage = pipeline.stage(second_context)
    second_promoted = pipeline.promote(second_context)

    assert second_stage.staged_rows == 6
    assert second_stage.rejected_rows == 1
    assert second_promoted == 3

    with engine.connect() as connection:
        admissions_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_admissions_yearly
                WHERE urn IN ('100001', '100002', '100003')
                """
            )
        ).scalar_one()
        assert admissions_rows == 3
