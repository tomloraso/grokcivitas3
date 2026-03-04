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
from civitas.infrastructure.pipelines.dfe_characteristics import (
    BRONZE_FILE_NAME,
    DFE_BACKFILL_MANIFEST_FILE_NAME,
    DfeCharacteristicsPipeline,
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
    reason="Postgres database unavailable for DfE characteristics integration test.",
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


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM school_demographics_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM schools
                WHERE urn IN ('100001', '100002')
                """
            )
        )


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


def _build_context(bronze_root: Path) -> PipelineRunContext:
    return PipelineRunContext(
        run_id=uuid4(),
        source=PipelineSource.DFE_CHARACTERISTICS,
        started_at=datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _copy_fixture_to_bronze(context: PipelineRunContext) -> None:
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "dfe_characteristics"
        / "school_characteristics_mixed.csv"
    )
    context.bronze_source_path.mkdir(parents=True, exist_ok=True)
    target = context.bronze_source_path / BRONZE_FILE_NAME
    target.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")


def _copy_backfill_fixtures_to_bronze(context: PipelineRunContext) -> None:
    context.bronze_source_path.mkdir(parents=True, exist_ok=True)
    header = "school_urn,time_period,ptfsm6cla1a,psenelek,psenelk,psenele,ptealgrp2,ptealgrp1,ptealgrp3\n"
    assets = [
        {
            "bronze_file_name": "school_characteristics_2022_23.csv",
            "source_dataset_id": "dataset-2023",
            "source_dataset_version": "v2023",
            "source_academic_year": "2022/23",
            "rows": ("100001,2022/23,21.0,13.2,10.2,3.0,10.0,87.5,2.5\n",),
        },
        {
            "bronze_file_name": "school_characteristics_2023_24.csv",
            "source_dataset_id": "dataset-2024",
            "source_dataset_version": "v2024",
            "source_academic_year": "2023/24",
            "rows": (
                "100001,2023/24,19.5,12.8,10.1,2.7,9.5,88.0,2.5\n",
                "100002,2023/24,22.1,15.4,12.0,3.4,12.2,84.6,3.2\n",
            ),
        },
        {
            "bronze_file_name": "school_characteristics_2024_25.csv",
            "source_dataset_id": "dataset-2025",
            "source_dataset_version": "v2025",
            "source_academic_year": "2024/25",
            "rows": (
                "100001,2024/25,18.0,12.0,9.7,2.3,8.8,89.4,1.8\n",
                "100002,2024/25,20.2,14.8,11.6,3.2,11.1,85.7,3.2\n",
            ),
        },
    ]

    for asset in assets:
        asset_path = context.bronze_source_path / asset["bronze_file_name"]
        asset_path.write_text(header + "".join(asset["rows"]), encoding="utf-8")

    manifest_payload = {
        "assets": [
            {
                "bronze_file_name": asset["bronze_file_name"],
                "source_reference": f"https://api.education.gov.uk/statistics/v1/data-sets/{asset['source_dataset_id']}/csv",
                "source_dataset_id": asset["source_dataset_id"],
                "source_dataset_version": asset["source_dataset_version"],
                "source_academic_year": asset["source_academic_year"],
            }
            for asset in assets
        ]
    }
    (context.bronze_source_path / DFE_BACKFILL_MANIFEST_FILE_NAME).write_text(
        json.dumps(manifest_payload),
        encoding="utf-8",
    )


def test_dfe_characteristics_pipeline_stage_and_promote_are_idempotent(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    _seed_schools(engine)

    pipeline = DfeCharacteristicsPipeline(
        engine=engine,
        source_csv=None,
        source_dataset_id="dataset-1",
    )

    first_context = _build_context(bronze_root)
    _copy_fixture_to_bronze(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 2
    assert first_stage.rejected_rows == 3

    first_promoted_rows = pipeline.promote(first_context)
    assert first_promoted_rows == 2

    with engine.connect() as connection:
        staged_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_demographics_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert staged_rows == 2

        suppressed_value = connection.execute(
            text(
                """
                SELECT disadvantaged_pct
                FROM school_demographics_yearly
                WHERE urn = '100002' AND academic_year = '2023/24'
                """
            )
        ).scalar_one()
        assert suppressed_value is None

        deduplicated_value = connection.execute(
            text(
                """
                SELECT disadvantaged_pct
                FROM school_demographics_yearly
                WHERE urn = '100001' AND academic_year = '2024/25'
                """
            )
        ).scalar_one()
        assert deduplicated_value == 18.8

        coverage_flags = connection.execute(
            text(
                """
                SELECT has_ethnicity_data, has_top_languages_data
                FROM school_demographics_yearly
                WHERE urn = '100001' AND academic_year = '2024/25'
                """
            )
        ).one()
        assert coverage_flags == (False, False)

        rejection_reason_codes = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT reason_code
                    FROM pipeline_rejections
                    WHERE run_id = :run_id
                    """
                ),
                {"run_id": str(first_context.run_id)},
            )
        }
        assert rejection_reason_codes == {
            "missing_urn",
            "invalid_academic_year",
            "invalid_sen_pct",
        }

    second_context = _build_context(bronze_root)
    _insert_run_row(engine, second_context)
    second_stage = pipeline.stage(second_context)
    assert second_stage.staged_rows == 2
    assert second_stage.rejected_rows == 3

    second_promoted_rows = pipeline.promote(second_context)
    assert second_promoted_rows == 2

    with engine.connect() as connection:
        total_rows_after_second_run = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_demographics_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert total_rows_after_second_run == 2


def test_dfe_characteristics_backfill_mode_respects_lookback_and_provenance(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    _seed_schools(engine)

    pipeline = DfeCharacteristicsPipeline(
        engine=engine,
        source_csv=None,
        source_dataset_id="dataset-2025",
        backfill_enabled=True,
        lookback_years=2,
    )

    first_context = _build_context(bronze_root)
    _copy_backfill_fixtures_to_bronze(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 4
    assert first_stage.rejected_rows == 0

    first_promoted_rows = pipeline.promote(first_context)
    assert first_promoted_rows == 4

    with engine.connect() as connection:
        promoted_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_demographics_yearly
                WHERE urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert promoted_rows == 4

        historical_gap = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM school_demographics_yearly
                WHERE academic_year = '2022/23'
                  AND urn IN ('100001', '100002')
                """
            )
        ).scalar_one()
        assert historical_gap == 0

        provenance_rows = connection.execute(
            text(
                """
                SELECT academic_year, source_dataset_id, source_dataset_version
                FROM school_demographics_yearly
                WHERE urn = '100001'
                ORDER BY academic_year
                """
            )
        ).all()
        assert provenance_rows == [
            ("2023/24", "dataset-2024", "v2024"),
            ("2024/25", "dataset-2025", "v2025"),
        ]

    second_context = _build_context(bronze_root)
    _insert_run_row(engine, second_context)

    second_stage = pipeline.stage(second_context)
    assert second_stage.staged_rows == 4
    assert second_stage.rejected_rows == 0

    second_promoted_rows = pipeline.promote(second_context)
    assert second_promoted_rows == 4

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
        assert total_rows == 4
