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
from civitas.infrastructure.pipelines.demographics_release_files import (
    BRONZE_MANIFEST_FILE_NAME,
    DemographicsReleaseFilesPipeline,
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
    reason="Postgres database unavailable for demographics release files integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    engine = _build_engine(DATABASE_URL)
    _ensure_schema(engine)
    _cleanup(engine)
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


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM school_home_language_yearly WHERE urn IN ('100001', '100002')")
        )
        connection.execute(
            text("DELETE FROM school_send_primary_need_yearly WHERE urn IN ('100001', '100002')")
        )
        connection.execute(
            text("DELETE FROM school_ethnicity_yearly WHERE urn IN ('100001', '100002')")
        )
        connection.execute(
            text("DELETE FROM school_demographics_yearly WHERE urn IN ('100001', '100002')")
        )
        connection.execute(text("DELETE FROM schools WHERE urn IN ('100001', '100002')"))


def _seed_schools(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO schools (
                    urn, name, phase, type, status, postcode,
                    easting, northing, location, updated_at
                ) VALUES
                (
                    '100001', 'Alpha Primary', 'Primary', 'Community school', 'Open', 'SW1A 1AA',
                    529090, 179645,
                    ST_GeogFromText('SRID=4326;POINT(-0.141 51.501)'),
                    timezone('utc', now())
                ),
                (
                    '100002', 'Beta Primary', 'Primary', 'Community school', 'Open', 'SW1A 2AA',
                    529200, 179700,
                    ST_GeogFromText('SRID=4326;POINT(-0.140 51.502)'),
                    timezone('utc', now())
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
        source=PipelineSource.DFE_CHARACTERISTICS,
        started_at=datetime(2026, 3, 4, 12, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _write_manifest_and_files(context: PipelineRunContext) -> None:
    context.bronze_source_path.mkdir(parents=True, exist_ok=True)

    spc_name = "spc_2024_25_spc-file-2024.csv"
    sen_name = "sen_2024_25_sen-file-2024.csv"

    (context.bronze_source_path / spc_name).write_text(
        "urn,time_period,% of pupils known to be eligible for free school meals,"
        "% of pupils known to be eligible for free school meals (Performance Tables),"
        "% of pupils whose first language is known or believed to be other than English,"
        "% of pupils whose first language is known or believed to be English,"
        "% of pupils whose first language is unclassified,"
        "% of pupils who are male,"
        "% of pupils who are female,"
        "% of pupils who are mobile,"
        "number of pupils whose first language is Somali,"
        "% of pupils whose first language is Somali,"
        "number of pupils whose first language is Polish,"
        "% of pupils whose first language is Polish,"
        "number of pupils classified as white British ethnic origin,"
        "% of pupils classified as white British ethnic origin,"
        "number of pupils classified as Irish ethnic origin,"
        "% of pupils classified as Irish ethnic origin,"
        "number of pupils classified as traveller of Irish heritage ethnic origin,"
        "% of pupils classified as traveller of Irish heritage ethnic origin,"
        "number of pupils classified as any other white background ethnic origin,"
        "% of pupils classified as any other white background ethnic origin,"
        "number of pupils classified as Gypsy/Roma ethnic origin,"
        "% of pupils classified as Gypsy/Roma ethnic origin,"
        "number of pupils classified as white and black Caribbean ethnic origin,"
        "% of pupils classified as white and black Caribbean ethnic origin,"
        "number of pupils classified as white and black African ethnic origin,"
        "% of pupils classified as white and black African ethnic origin,"
        "number of pupils classified as white and Asian ethnic origin,"
        "% of pupils classified as white and Asian ethnic origin,"
        "number of pupils classified as any other mixed background ethnic origin,"
        "% of pupils classified as any other mixed background ethnic origin,"
        "number of pupils classified as Indian ethnic origin,"
        "% of pupils classified as Indian ethnic origin,"
        "number of pupils classified as Pakistani ethnic origin,"
        "% of pupils classified as Pakistani ethnic origin,"
        "number of pupils classified as Bangladeshi ethnic origin,"
        "% of pupils classified as Bangladeshi ethnic origin,"
        "number of pupils classified as any other Asian background ethnic origin,"
        "% of pupils classified as any other Asian background ethnic origin,"
        "number of pupils classified as Caribbean ethnic origin,"
        "% of pupils classified as Caribbean ethnic origin,"
        "number of pupils classified as African ethnic origin,"
        "% of pupils classified as African ethnic origin,"
        "number of pupils classified as any other black background ethnic origin,"
        "% of pupils classified as any other black background ethnic origin,"
        "number of pupils classified as Chinese ethnic origin,"
        "% of pupils classified as Chinese ethnic origin,"
        "number of pupils classified as any other ethnic group ethnic origin,"
        "% of pupils classified as any other ethnic group ethnic origin,"
        "number of pupils unclassified,"
        "% of pupils unclassified\n"
        "100001,202324,19.1,19.5,9.5,88.0,2.5,49.3,50.7,3.2,18,7.5,12,5.0,101,50.5,2,1.0,1,0.5,5,2.5,1,0.5,4,2.0,2,1.0,4,2.0,3,1.5,14,7.0,10,5.0,8,4.0,6,3.0,5,2.5,12,6.0,3,1.5,4,2.0,8,4.0,9,4.5\n"
        "100001,202425,17.2,18.0,8.8,89.4,1.8,49.1,50.9,2.8,17,6.8,13,5.2,98,49.0,2,1.0,1,0.5,5,2.5,1,0.5,4,2.0,2,1.0,4,2.0,3,1.5,14,7.0,10,5.0,8,4.0,6,3.0,5,2.5,12,6.0,3,1.5,4,2.0,8,4.0,8,4.0\n"
        "100002,202425,SUPP,SUPP,11.1,85.7,3.2,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP,SUPP\n"
        ",202425,18.2,18.2,9.0,90.0,1.0,49.0,51.0,2.0,20,8.0,11,4.4,98,49.0,2,1.0,1,0.5,5,2.5,1,0.5,4,2.0,2,1.0,4,2.0,3,1.5,14,7.0,10,5.0,8,4.0,6,3.0,5,2.5,12,6.0,3,1.5,4,2.0,8,4.0,8,4.0\n",
        encoding="utf-8",
    )

    (context.bronze_source_path / sen_name).write_text(
        "URN,time_period,Total pupils,SEN support,EHC plan,"
        "number of pupils with specific learning difficulty as primary need,"
        "% of pupils with specific learning difficulty as primary need,"
        "number of pupils with speech language and communication needs as primary need,"
        "% of pupils with speech language and communication needs as primary need\n"
        "100001,202324,240,36,9,12,5.0,8,3.3\n"
        "100001,202425,250,37,11,14,5.6,9,3.6\n"
        "100002,202425,200,40,8,9,4.5,6,3.0\n"
        "100002,202325,oops,35,7,8,4.0,5,2.5\n",
        encoding="utf-8",
    )

    manifest_payload = {
        "normalization_contract_version": "demographics_release_files.v1",
        "lookback_years": 1,
        "assets": [
            {
                "family": "spc",
                "publication_slug": "school-pupils-and-their-characteristics",
                "release_slug": "2024-25",
                "release_version_id": "spc-rv-2024",
                "file_id": "spc-file-2024",
                "file_name": "School level underlying data 2025",
                "bronze_file_name": spc_name,
                "downloaded_at": "2026-03-04T12:00:00+00:00",
                "sha256": "sha-spc",
                "row_count": 4,
            },
            {
                "family": "sen",
                "publication_slug": "special-educational-needs-in-england",
                "release_slug": "2024-25",
                "release_version_id": "sen-rv-2024",
                "file_id": "sen-file-2024",
                "file_name": "School level underlying data 2025",
                "bronze_file_name": sen_name,
                "downloaded_at": "2026-03-04T12:00:00+00:00",
                "sha256": "sha-sen",
                "row_count": 4,
            },
        ],
    }
    (context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME).write_text(
        json.dumps(manifest_payload),
        encoding="utf-8",
    )


def test_demographics_release_files_pipeline_stage_and_promote_are_idempotent(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    _seed_schools(engine)

    pipeline = DemographicsReleaseFilesPipeline(
        engine=engine,
        spc_publication_slug="school-pupils-and-their-characteristics",
        sen_publication_slug="special-educational-needs-in-england",
        release_slugs=("2024-25",),
        lookback_years=1,
    )

    first_context = _context(bronze_root)
    _write_manifest_and_files(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 3
    assert first_stage.rejected_rows == 2

    first_promoted = pipeline.promote(first_context)
    assert first_promoted == 3

    with engine.connect() as connection:
        total_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_demographics_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert total_rows == 3

        row_202425 = connection.execute(
            text(
                """
                SELECT
                    fsm_pct,
                    fsm6_pct,
                    disadvantaged_pct,
                    male_pct,
                    female_pct,
                    pupil_mobility_pct,
                    has_fsm6_data,
                    has_gender_data,
                    has_mobility_data,
                    has_send_primary_need_data,
                    has_top_languages_data,
                    sen_pct,
                    ehcp_pct,
                    total_pupils,
                    source_dataset_id,
                    has_ethnicity_data
                FROM school_demographics_yearly
                WHERE urn = '100001' AND academic_year = '2024/25'
                """
            )
        ).one()
        assert row_202425[0] == 17.2
        assert row_202425[1] == 18.0
        assert row_202425[2] == 18.0
        assert row_202425[3] == 49.1
        assert row_202425[4] == 50.9
        assert row_202425[5] == 2.8
        assert row_202425[6] is True
        assert row_202425[7] is True
        assert row_202425[8] is True
        assert row_202425[9] is True
        assert row_202425[10] is True
        assert row_202425[11] == pytest.approx(14.8)
        assert row_202425[12] == pytest.approx(4.4)
        assert row_202425[13] == 250
        assert "spc:spc-rv-2024" in row_202425[14]
        assert "sen:sen-rv-2024" in row_202425[14]
        assert row_202425[15] is True

        row_partial = connection.execute(
            text(
                """
                SELECT disadvantaged_pct, sen_pct, has_ethnicity_data
                FROM school_demographics_yearly
                WHERE urn = '100002' AND academic_year = '2024/25'
                """
            )
        ).one()
        assert row_partial[0] is None
        assert row_partial[1] == pytest.approx(20.0)
        assert row_partial[2] is False

        send_need_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_send_primary_need_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert send_need_count == 6

        top_language_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_home_language_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert top_language_count == 4

        ethnicity_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_ethnicity_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert ethnicity_count == 2

        ethnicity_row = connection.execute(
            text(
                """
                SELECT white_british_pct, white_british_count, unclassified_pct, unclassified_count
                FROM school_ethnicity_yearly
                WHERE urn = '100001' AND academic_year = '2024/25'
                """
            )
        ).one()
        assert ethnicity_row[0] == 49.0
        assert ethnicity_row[1] == 98
        assert ethnicity_row[2] == 4.0
        assert ethnicity_row[3] == 8

    second_context = _context(bronze_root)
    _insert_run_row(engine, second_context)
    second_stage = pipeline.stage(second_context)
    second_promoted = pipeline.promote(second_context)

    assert second_stage.staged_rows == 3
    assert second_promoted == 3

    with engine.connect() as connection:
        total_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_demographics_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert total_rows == 3
        ethnicity_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_ethnicity_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert ethnicity_rows == 2
