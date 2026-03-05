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
from civitas.infrastructure.pipelines.uk_house_prices import (
    BRONZE_FILE_NAME,
    BRONZE_METADATA_FILE_NAME,
    UkHousePricesPipeline,
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
    reason="Postgres database unavailable for UK house-prices pipeline integration test.",
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
                CREATE TABLE IF NOT EXISTS area_house_price_context (
                    area_code text NOT NULL,
                    area_name text NOT NULL,
                    month date NOT NULL,
                    average_price double precision NOT NULL,
                    monthly_change_pct double precision NULL,
                    annual_change_pct double precision NULL,
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


def _cleanup(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM pipeline_rejections
                WHERE source = 'uk_house_prices'
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM pipeline_runs
                WHERE source = 'uk_house_prices'
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM area_house_price_context
                WHERE area_code IN ('E09000033', 'E08000001')
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
        source=PipelineSource.UK_HOUSE_PRICES,
        started_at=datetime(2026, 3, 5, 19, 15, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _write_fixture_to_bronze(context: PipelineRunContext) -> None:
    context.bronze_source_path.mkdir(parents=True, exist_ok=True)
    (context.bronze_source_path / BRONZE_FILE_NAME).write_text(
        "Date,Region_Name,Area_Code,Average_Price,Monthly_Change,Annual_Change\n"
        "2026-01-01,Westminster,E09000033,810000,0.5,6.0\n"
        "2026-01-01,Westminster,E09000033,811000,0.6,6.2\n"
        "2026-01-01,Liverpool,E08000001,205000,N/A,.\n"
        "2026-01-01,Missing Area,,199000,0.1,1.2\n"
        "2026/01/01,Bad Date,E09000033,100000,0.1,1.0\n",
        encoding="utf-8",
    )
    (context.bronze_source_path / BRONZE_METADATA_FILE_NAME).write_text(
        json.dumps(
            {
                "source_file_url": (
                    "https://publicdata.landregistry.gov.uk/market-trend-data/"
                    "house-price-index-data/Average-prices-2026-01.csv"
                ),
                "source_month": "2026-01",
                "normalization_contract_version": "uk_house_prices.v1",
            }
        ),
        encoding="utf-8",
    )


def test_uk_house_prices_pipeline_stage_and_promote_are_idempotent(
    engine: Engine,
    tmp_path: Path,
) -> None:
    bronze_root = tmp_path / "bronze"
    pipeline = UkHousePricesPipeline(engine=engine)

    first_context = _context(bronze_root)
    _write_fixture_to_bronze(first_context)
    _insert_run_row(engine, first_context)

    first_stage = pipeline.stage(first_context)
    assert first_stage.staged_rows == 2
    assert first_stage.rejected_rows == 2
    assert first_stage.contract_version == "uk_house_prices.v1+2026-01"

    first_promoted = pipeline.promote(first_context)
    assert first_promoted == 2

    with engine.connect() as connection:
        total_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM area_house_price_context
                WHERE area_code IN ('E09000033', 'E08000001')
                """
            )
        ).scalar_one()
        assert total_rows == 2

        westminster = connection.execute(
            text(
                """
                SELECT
                    area_name,
                    average_price,
                    monthly_change_pct,
                    annual_change_pct,
                    source_dataset_id,
                    source_dataset_version,
                    source_file_url
                FROM area_house_price_context
                WHERE area_code = 'E09000033' AND month = '2026-01-01'
                """
            )
        ).one()
        assert westminster[0] == "Westminster"
        assert westminster[1] == pytest.approx(811000.0)
        assert westminster[2] == pytest.approx(0.6)
        assert westminster[3] == pytest.approx(6.2)
        assert westminster[4] == "uk_hpi_average_price"
        assert westminster[5] == "2026-01"
        assert "Average-prices-2026-01.csv" in westminster[6]

        liverpool = connection.execute(
            text(
                """
                SELECT monthly_change_pct, annual_change_pct
                FROM area_house_price_context
                WHERE area_code = 'E08000001' AND month = '2026-01-01'
                """
            )
        ).one()
        assert liverpool[0] is None
        assert liverpool[1] is None

        rejection_reasons = {
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
        assert rejection_reasons == {"missing_area_code", "invalid_month"}

    second_context = _context(bronze_root)
    _insert_run_row(engine, second_context)

    second_stage = pipeline.stage(second_context)
    assert second_stage.staged_rows == 2
    assert second_stage.rejected_rows == 2

    second_promoted = pipeline.promote(second_context)
    assert second_promoted == 2

    with engine.connect() as connection:
        total_rows_after_second = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM area_house_price_context
                WHERE area_code IN ('E09000033', 'E08000001')
                """
            )
        ).scalar_one()
        assert total_rows_after_second == 2
