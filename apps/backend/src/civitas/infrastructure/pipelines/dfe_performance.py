from __future__ import annotations

import gzip
import hashlib
import json
import urllib.request
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, TypedDict

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import dfe_performance as performance_contract

DFE_BASE_URL = "https://api.education.gov.uk/statistics/v1"
DFE_DATASET_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}"
DFE_DATASET_META_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}/meta"
DFE_DATASET_QUERY_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}/query"

BRONZE_MANIFEST_FILE_NAME = "dfe_performance.manifest.json"
DEFAULT_LOOKBACK_YEARS = 3
DEFAULT_PAGE_SIZE = 10_000
MAX_PAGE_SIZE = 10_000


@dataclass(frozen=True)
class DfePerformanceStagedRow:
    urn: str
    academic_year: str
    attainment8_average: float | None
    progress8_average: float | None
    progress8_disadvantaged: float | None
    progress8_not_disadvantaged: float | None
    progress8_disadvantaged_gap: float | None
    engmath_5_plus_pct: float | None
    engmath_4_plus_pct: float | None
    ebacc_entry_pct: float | None
    ebacc_5_plus_pct: float | None
    ebacc_4_plus_pct: float | None
    ks2_reading_expected_pct: float | None
    ks2_writing_expected_pct: float | None
    ks2_maths_expected_pct: float | None
    ks2_combined_expected_pct: float | None
    ks2_reading_higher_pct: float | None
    ks2_writing_higher_pct: float | None
    ks2_maths_higher_pct: float | None
    ks2_combined_higher_pct: float | None
    ks2_source_dataset_id: str | None
    ks2_source_dataset_version: str | None
    ks4_source_dataset_id: str | None
    ks4_source_dataset_version: str | None


@dataclass(frozen=True)
class _DatasetDownload:
    dataset_key: str
    dataset_id: str
    dataset_version: str | None
    meta_file_name: str
    page_files: tuple[str, ...]
    rows: int
    assets: tuple[dict[str, object], ...]


@dataclass
class _PerformanceAccumulator:
    urn: str
    academic_year: str
    attainment8_average: float | None = None
    progress8_average: float | None = None
    progress8_disadvantaged: float | None = None
    progress8_not_disadvantaged: float | None = None
    engmath_5_plus_pct: float | None = None
    engmath_4_plus_pct: float | None = None
    ebacc_entry_pct: float | None = None
    ebacc_5_plus_pct: float | None = None
    ebacc_4_plus_pct: float | None = None
    ks2_reading_expected_pct: float | None = None
    ks2_writing_expected_pct: float | None = None
    ks2_maths_expected_pct: float | None = None
    ks2_combined_expected_pct: float | None = None
    ks2_reading_higher_pct: float | None = None
    ks2_writing_higher_pct: float | None = None
    ks2_maths_higher_pct: float | None = None
    ks2_combined_higher_pct: float | None = None
    ks2_source_dataset_id: str | None = None
    ks2_source_dataset_version: str | None = None
    ks4_source_dataset_id: str | None = None
    ks4_source_dataset_version: str | None = None


class _ManifestDataset(TypedDict):
    dataset_id: str
    dataset_version: str | None
    meta_file_name: str
    page_files: tuple[str, ...]


class DfePerformancePipeline:
    source = PipelineSource.DFE_PERFORMANCE

    def __init__(
        self,
        engine: Engine,
        *,
        ks2_dataset_id: str,
        ks4_dataset_id: str,
        lookback_years: int = DEFAULT_LOOKBACK_YEARS,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> None:
        if lookback_years <= 0:
            raise ValueError("DfE performance lookback years must be greater than 0.")
        if page_size <= 0 or page_size > MAX_PAGE_SIZE:
            raise ValueError(f"DfE performance page size must be between 1 and {MAX_PAGE_SIZE}.")
        self._engine = engine
        self._ks2_dataset_id = ks2_dataset_id.strip()
        self._ks4_dataset_id = ks4_dataset_id.strip()
        self._lookback_years = lookback_years
        self._page_size = page_size

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME

        existing_manifest = _load_json_dict(manifest_path)
        if _manifest_assets_exist(existing_manifest, bronze_source_path=context.bronze_source_path):
            cached_rows = _parse_int(existing_manifest.get("rows"))
            if cached_rows is not None:
                return cached_rows

        _clear_existing_bronze_files(context.bronze_source_path)

        ks2_download = self._download_dataset(
            context=context,
            dataset_key="ks2",
            dataset_id=self._ks2_dataset_id,
            indicators=tuple(performance_contract.KS2_INDICATOR_IDS.values()),
        )
        ks4_download = self._download_dataset(
            context=context,
            dataset_key="ks4",
            dataset_id=self._ks4_dataset_id,
            indicators=tuple(performance_contract.KS4_INDICATOR_IDS.values()),
        )

        total_rows = ks2_download.rows + ks4_download.rows
        manifest_payload = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "normalization_contract_version": performance_contract.CONTRACT_VERSION,
            "lookback_years": self._lookback_years,
            "rows": total_rows,
            "datasets": [
                {
                    "dataset_key": ks2_download.dataset_key,
                    "dataset_id": ks2_download.dataset_id,
                    "dataset_version": ks2_download.dataset_version,
                    "meta_file_name": ks2_download.meta_file_name,
                    "page_files": list(ks2_download.page_files),
                    "rows": ks2_download.rows,
                },
                {
                    "dataset_key": ks4_download.dataset_key,
                    "dataset_id": ks4_download.dataset_id,
                    "dataset_version": ks4_download.dataset_version,
                    "meta_file_name": ks4_download.meta_file_name,
                    "page_files": list(ks4_download.page_files),
                    "rows": ks4_download.rows,
                },
            ],
            "assets": [*ks2_download.assets, *ks4_download.assets],
        }
        manifest_path.write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return total_rows

    def stage(self, context: PipelineRunContext) -> StageResult:
        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
        manifest_payload = _load_json_dict(manifest_path)
        if not manifest_payload:
            raise FileNotFoundError(
                f"DfE performance manifest not found at '{manifest_path}'. Run download stage first."
            )

        dataset_payloads = _parse_manifest_datasets(manifest_payload)
        ks2_dataset = dataset_payloads.get("ks2")
        ks4_dataset = dataset_payloads.get("ks4")
        if ks2_dataset is None or ks4_dataset is None:
            raise ValueError("DfE performance manifest is missing ks2/ks4 dataset entries.")

        ks2_urn_lookup = _school_location_urn_lookup(
            _load_json_dict(context.bronze_source_path / ks2_dataset["meta_file_name"])
        )
        ks4_urn_lookup = _school_location_urn_lookup(
            _load_json_dict(context.bronze_source_path / ks4_dataset["meta_file_name"])
        )

        rows_by_key: dict[tuple[str, str], _PerformanceAccumulator] = {}
        rejected_rows: list[tuple[str, dict[str, object]]] = []

        ks4_filter_id = performance_contract.KS4_FILTER_IDS["disadvantage_status"]
        ks4_first_language_filter_id = performance_contract.KS4_FILTER_IDS["first_language"]
        ks4_mobility_filter_id = performance_contract.KS4_FILTER_IDS["mobility_status"]
        ks4_sex_filter_id = performance_contract.KS4_FILTER_IDS["sex"]
        ks4_total_option = performance_contract.KS4_FILTER_OPTION_IDS["disadvantage_total"]
        ks4_disadvantaged_option = performance_contract.KS4_FILTER_OPTION_IDS[
            "disadvantage_disadvantaged"
        ]
        ks4_not_disadvantaged_option = performance_contract.KS4_FILTER_OPTION_IDS[
            "disadvantage_not_disadvantaged"
        ]
        ks4_total_first_language = performance_contract.KS4_FILTER_OPTION_IDS[
            "first_language_total"
        ]
        ks4_total_mobility = performance_contract.KS4_FILTER_OPTION_IDS["mobility_total"]
        ks4_total_sex = performance_contract.KS4_FILTER_OPTION_IDS["sex_total"]

        for page_file_name in ks4_dataset["page_files"]:
            page_payload = _load_json_dict(context.bronze_source_path / page_file_name)
            for raw_result in _as_list(page_payload.get("results")):
                result = _as_dict(raw_result)
                filters = _as_dict(result.get("filters"))
                if _as_str(filters.get(ks4_first_language_filter_id)) != ks4_total_first_language:
                    continue
                if _as_str(filters.get(ks4_mobility_filter_id)) != ks4_total_mobility:
                    continue
                if _as_str(filters.get(ks4_sex_filter_id)) != ks4_total_sex:
                    continue

                normalized_key, rejection = _normalize_result_key(result, urn_lookup=ks4_urn_lookup)
                if normalized_key is None:
                    if rejection is not None:
                        rejected_rows.append((rejection, result))
                    continue

                urn, academic_year = normalized_key
                accumulator = rows_by_key.setdefault(
                    (urn, academic_year),
                    _PerformanceAccumulator(urn=urn, academic_year=academic_year),
                )
                accumulator.ks4_source_dataset_id = ks4_dataset["dataset_id"]
                accumulator.ks4_source_dataset_version = ks4_dataset["dataset_version"]

                disadvantaged_option = _as_str(filters.get(ks4_filter_id))
                values = _as_dict(result.get("values"))
                if disadvantaged_option == ks4_total_option:
                    parsed = _parse_ks4_total_values(values)
                    if parsed is None:
                        rejected_rows.append(("invalid_ks4_total_values", result))
                        continue
                    accumulator.attainment8_average = parsed["attainment8_average"]
                    accumulator.progress8_average = parsed["progress8_average"]
                    accumulator.engmath_5_plus_pct = parsed["engmath_5_plus_pct"]
                    accumulator.engmath_4_plus_pct = parsed["engmath_4_plus_pct"]
                    accumulator.ebacc_entry_pct = parsed["ebacc_entry_pct"]
                    accumulator.ebacc_5_plus_pct = parsed["ebacc_5_plus_pct"]
                    accumulator.ebacc_4_plus_pct = parsed["ebacc_4_plus_pct"]
                    continue

                progress8_value = _parse_optional_numeric(
                    values.get(performance_contract.KS4_INDICATOR_IDS["progress8_average"])
                )
                if disadvantaged_option == ks4_disadvantaged_option:
                    accumulator.progress8_disadvantaged = progress8_value
                    continue
                if disadvantaged_option == ks4_not_disadvantaged_option:
                    accumulator.progress8_not_disadvantaged = progress8_value
                    continue

        ks2_breakdown_filter_id = performance_contract.KS2_FILTER_IDS["breakdown"]
        ks2_subject_filter_id = performance_contract.KS2_FILTER_IDS["subject"]
        ks2_total_breakdown = performance_contract.KS2_FILTER_OPTION_IDS["breakdown_total"]
        ks2_subject_to_metric_key = {
            performance_contract.KS2_FILTER_OPTION_IDS["subject_reading"]: "reading",
            performance_contract.KS2_FILTER_OPTION_IDS["subject_writing"]: "writing",
            performance_contract.KS2_FILTER_OPTION_IDS["subject_maths"]: "maths",
            performance_contract.KS2_FILTER_OPTION_IDS["subject_combined"]: "combined",
        }

        for page_file_name in ks2_dataset["page_files"]:
            page_payload = _load_json_dict(context.bronze_source_path / page_file_name)
            for raw_result in _as_list(page_payload.get("results")):
                result = _as_dict(raw_result)
                filters = _as_dict(result.get("filters"))
                if _as_str(filters.get(ks2_breakdown_filter_id)) != ks2_total_breakdown:
                    continue

                subject_option = _as_str(filters.get(ks2_subject_filter_id))
                if subject_option is None:
                    continue
                metric_key = ks2_subject_to_metric_key.get(subject_option)
                if metric_key is None:
                    continue

                normalized_key, rejection = _normalize_result_key(result, urn_lookup=ks2_urn_lookup)
                if normalized_key is None:
                    if rejection is not None:
                        rejected_rows.append((rejection, result))
                    continue

                values = _as_dict(result.get("values"))
                expected_value = _parse_optional_numeric(
                    values.get(performance_contract.KS2_INDICATOR_IDS["expected_standard_pct"])
                )
                higher_value = _parse_optional_numeric(
                    values.get(performance_contract.KS2_INDICATOR_IDS["higher_standard_pct"])
                )

                urn, academic_year = normalized_key
                accumulator = rows_by_key.setdefault(
                    (urn, academic_year),
                    _PerformanceAccumulator(urn=urn, academic_year=academic_year),
                )
                accumulator.ks2_source_dataset_id = ks2_dataset["dataset_id"]
                accumulator.ks2_source_dataset_version = ks2_dataset["dataset_version"]

                if metric_key == "reading":
                    accumulator.ks2_reading_expected_pct = expected_value
                    accumulator.ks2_reading_higher_pct = higher_value
                elif metric_key == "writing":
                    accumulator.ks2_writing_expected_pct = expected_value
                    accumulator.ks2_writing_higher_pct = higher_value
                elif metric_key == "maths":
                    accumulator.ks2_maths_expected_pct = expected_value
                    accumulator.ks2_maths_higher_pct = higher_value
                elif metric_key == "combined":
                    accumulator.ks2_combined_expected_pct = expected_value
                    accumulator.ks2_combined_higher_pct = higher_value

        selected_years = _select_lookback_years(
            years=tuple({row.academic_year for row in rows_by_key.values()}),
            lookback_years=self._lookback_years,
        )
        staged_rows = [
            _to_staged_row(row)
            for row in rows_by_key.values()
            if row.academic_year in selected_years
        ]
        staged_rows.sort(
            key=lambda row: (row.urn, _academic_year_sort_key(row.academic_year), row.academic_year)
        )

        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
            connection.execute(
                text(
                    f"""
                    CREATE TABLE staging.{staging_table_name} (
                        urn text NOT NULL,
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
                        PRIMARY KEY (urn, academic_year)
                    )
                    """
                )
            )
            if staged_rows:
                staged_insert = text(
                    f"""
                    INSERT INTO staging.{staging_table_name} (
                        urn,
                        academic_year,
                        attainment8_average,
                        progress8_average,
                        progress8_disadvantaged,
                        progress8_not_disadvantaged,
                        progress8_disadvantaged_gap,
                        engmath_5_plus_pct,
                        engmath_4_plus_pct,
                        ebacc_entry_pct,
                        ebacc_5_plus_pct,
                        ebacc_4_plus_pct,
                        ks2_reading_expected_pct,
                        ks2_writing_expected_pct,
                        ks2_maths_expected_pct,
                        ks2_combined_expected_pct,
                        ks2_reading_higher_pct,
                        ks2_writing_higher_pct,
                        ks2_maths_higher_pct,
                        ks2_combined_higher_pct,
                        ks2_source_dataset_id,
                        ks2_source_dataset_version,
                        ks4_source_dataset_id,
                        ks4_source_dataset_version
                    ) VALUES (
                        :urn,
                        :academic_year,
                        :attainment8_average,
                        :progress8_average,
                        :progress8_disadvantaged,
                        :progress8_not_disadvantaged,
                        :progress8_disadvantaged_gap,
                        :engmath_5_plus_pct,
                        :engmath_4_plus_pct,
                        :ebacc_entry_pct,
                        :ebacc_5_plus_pct,
                        :ebacc_4_plus_pct,
                        :ks2_reading_expected_pct,
                        :ks2_writing_expected_pct,
                        :ks2_maths_expected_pct,
                        :ks2_combined_expected_pct,
                        :ks2_reading_higher_pct,
                        :ks2_writing_higher_pct,
                        :ks2_maths_higher_pct,
                        :ks2_combined_higher_pct,
                        :ks2_source_dataset_id,
                        :ks2_source_dataset_version,
                        :ks4_source_dataset_id,
                        :ks4_source_dataset_version
                    )
                    ON CONFLICT (urn, academic_year) DO UPDATE SET
                        attainment8_average = EXCLUDED.attainment8_average,
                        progress8_average = EXCLUDED.progress8_average,
                        progress8_disadvantaged = EXCLUDED.progress8_disadvantaged,
                        progress8_not_disadvantaged = EXCLUDED.progress8_not_disadvantaged,
                        progress8_disadvantaged_gap = EXCLUDED.progress8_disadvantaged_gap,
                        engmath_5_plus_pct = EXCLUDED.engmath_5_plus_pct,
                        engmath_4_plus_pct = EXCLUDED.engmath_4_plus_pct,
                        ebacc_entry_pct = EXCLUDED.ebacc_entry_pct,
                        ebacc_5_plus_pct = EXCLUDED.ebacc_5_plus_pct,
                        ebacc_4_plus_pct = EXCLUDED.ebacc_4_plus_pct,
                        ks2_reading_expected_pct = EXCLUDED.ks2_reading_expected_pct,
                        ks2_writing_expected_pct = EXCLUDED.ks2_writing_expected_pct,
                        ks2_maths_expected_pct = EXCLUDED.ks2_maths_expected_pct,
                        ks2_combined_expected_pct = EXCLUDED.ks2_combined_expected_pct,
                        ks2_reading_higher_pct = EXCLUDED.ks2_reading_higher_pct,
                        ks2_writing_higher_pct = EXCLUDED.ks2_writing_higher_pct,
                        ks2_maths_higher_pct = EXCLUDED.ks2_maths_higher_pct,
                        ks2_combined_higher_pct = EXCLUDED.ks2_combined_higher_pct,
                        ks2_source_dataset_id = EXCLUDED.ks2_source_dataset_id,
                        ks2_source_dataset_version = EXCLUDED.ks2_source_dataset_version,
                        ks4_source_dataset_id = EXCLUDED.ks4_source_dataset_id,
                        ks4_source_dataset_version = EXCLUDED.ks4_source_dataset_version
                    """
                )
                for rows_chunk in chunked(staged_rows, context.stage_chunk_size):
                    connection.execute(
                        staged_insert,
                        [
                            {
                                "urn": row.urn,
                                "academic_year": row.academic_year,
                                "attainment8_average": row.attainment8_average,
                                "progress8_average": row.progress8_average,
                                "progress8_disadvantaged": row.progress8_disadvantaged,
                                "progress8_not_disadvantaged": row.progress8_not_disadvantaged,
                                "progress8_disadvantaged_gap": row.progress8_disadvantaged_gap,
                                "engmath_5_plus_pct": row.engmath_5_plus_pct,
                                "engmath_4_plus_pct": row.engmath_4_plus_pct,
                                "ebacc_entry_pct": row.ebacc_entry_pct,
                                "ebacc_5_plus_pct": row.ebacc_5_plus_pct,
                                "ebacc_4_plus_pct": row.ebacc_4_plus_pct,
                                "ks2_reading_expected_pct": row.ks2_reading_expected_pct,
                                "ks2_writing_expected_pct": row.ks2_writing_expected_pct,
                                "ks2_maths_expected_pct": row.ks2_maths_expected_pct,
                                "ks2_combined_expected_pct": row.ks2_combined_expected_pct,
                                "ks2_reading_higher_pct": row.ks2_reading_higher_pct,
                                "ks2_writing_higher_pct": row.ks2_writing_higher_pct,
                                "ks2_maths_higher_pct": row.ks2_maths_higher_pct,
                                "ks2_combined_higher_pct": row.ks2_combined_higher_pct,
                                "ks2_source_dataset_id": row.ks2_source_dataset_id,
                                "ks2_source_dataset_version": row.ks2_source_dataset_version,
                                "ks4_source_dataset_id": row.ks4_source_dataset_id,
                                "ks4_source_dataset_version": row.ks4_source_dataset_version,
                            }
                            for row in rows_chunk
                        ],
                    )

            if rejected_rows:
                rejection_insert = text(
                    """
                    INSERT INTO pipeline_rejections (
                        run_id,
                        source,
                        stage,
                        reason_code,
                        raw_record
                    ) VALUES (
                        :run_id,
                        :source,
                        'stage',
                        :reason_code,
                        CAST(:raw_record AS jsonb)
                    )
                    """
                )
                for rejected_chunk in chunked(rejected_rows, context.stage_chunk_size):
                    connection.execute(
                        rejection_insert,
                        [
                            {
                                "run_id": str(context.run_id),
                                "source": context.source.value,
                                "reason_code": reason_code,
                                "raw_record": json.dumps(raw_row, ensure_ascii=True),
                            }
                            for reason_code, raw_row in rejected_chunk
                        ],
                    )

        return StageResult(
            staged_rows=len(staged_rows),
            rejected_rows=len(rejected_rows),
            contract_version=performance_contract.CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            promoted_rows = int(
                connection.execute(
                    text(
                        f"""
                        WITH upserted AS (
                            INSERT INTO school_performance_yearly (
                                urn,
                                academic_year,
                                attainment8_average,
                                progress8_average,
                                progress8_disadvantaged,
                                progress8_not_disadvantaged,
                                progress8_disadvantaged_gap,
                                engmath_5_plus_pct,
                                engmath_4_plus_pct,
                                ebacc_entry_pct,
                                ebacc_5_plus_pct,
                                ebacc_4_plus_pct,
                                ks2_reading_expected_pct,
                                ks2_writing_expected_pct,
                                ks2_maths_expected_pct,
                                ks2_combined_expected_pct,
                                ks2_reading_higher_pct,
                                ks2_writing_higher_pct,
                                ks2_maths_higher_pct,
                                ks2_combined_higher_pct,
                                ks2_source_dataset_id,
                                ks2_source_dataset_version,
                                ks4_source_dataset_id,
                                ks4_source_dataset_version,
                                updated_at
                            )
                            SELECT
                                staged.urn,
                                staged.academic_year,
                                staged.attainment8_average,
                                staged.progress8_average,
                                staged.progress8_disadvantaged,
                                staged.progress8_not_disadvantaged,
                                staged.progress8_disadvantaged_gap,
                                staged.engmath_5_plus_pct,
                                staged.engmath_4_plus_pct,
                                staged.ebacc_entry_pct,
                                staged.ebacc_5_plus_pct,
                                staged.ebacc_4_plus_pct,
                                staged.ks2_reading_expected_pct,
                                staged.ks2_writing_expected_pct,
                                staged.ks2_maths_expected_pct,
                                staged.ks2_combined_expected_pct,
                                staged.ks2_reading_higher_pct,
                                staged.ks2_writing_higher_pct,
                                staged.ks2_maths_higher_pct,
                                staged.ks2_combined_higher_pct,
                                staged.ks2_source_dataset_id,
                                staged.ks2_source_dataset_version,
                                staged.ks4_source_dataset_id,
                                staged.ks4_source_dataset_version,
                                timezone('utc', now())
                            FROM staging.{staging_table_name} AS staged
                            ON CONFLICT (urn, academic_year) DO UPDATE SET
                                attainment8_average = EXCLUDED.attainment8_average,
                                progress8_average = EXCLUDED.progress8_average,
                                progress8_disadvantaged = EXCLUDED.progress8_disadvantaged,
                                progress8_not_disadvantaged = EXCLUDED.progress8_not_disadvantaged,
                                progress8_disadvantaged_gap = EXCLUDED.progress8_disadvantaged_gap,
                                engmath_5_plus_pct = EXCLUDED.engmath_5_plus_pct,
                                engmath_4_plus_pct = EXCLUDED.engmath_4_plus_pct,
                                ebacc_entry_pct = EXCLUDED.ebacc_entry_pct,
                                ebacc_5_plus_pct = EXCLUDED.ebacc_5_plus_pct,
                                ebacc_4_plus_pct = EXCLUDED.ebacc_4_plus_pct,
                                ks2_reading_expected_pct = EXCLUDED.ks2_reading_expected_pct,
                                ks2_writing_expected_pct = EXCLUDED.ks2_writing_expected_pct,
                                ks2_maths_expected_pct = EXCLUDED.ks2_maths_expected_pct,
                                ks2_combined_expected_pct = EXCLUDED.ks2_combined_expected_pct,
                                ks2_reading_higher_pct = EXCLUDED.ks2_reading_higher_pct,
                                ks2_writing_higher_pct = EXCLUDED.ks2_writing_higher_pct,
                                ks2_maths_higher_pct = EXCLUDED.ks2_maths_higher_pct,
                                ks2_combined_higher_pct = EXCLUDED.ks2_combined_higher_pct,
                                ks2_source_dataset_id = EXCLUDED.ks2_source_dataset_id,
                                ks2_source_dataset_version = EXCLUDED.ks2_source_dataset_version,
                                ks4_source_dataset_id = EXCLUDED.ks4_source_dataset_id,
                                ks4_source_dataset_version = EXCLUDED.ks4_source_dataset_version,
                                updated_at = timezone('utc', now())
                            RETURNING 1
                        )
                        SELECT COUNT(*) FROM upserted
                        """
                    )
                ).scalar_one()
            )
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
        return promoted_rows

    @staticmethod
    def _staging_table_name(context: PipelineRunContext) -> str:
        return f"dfe_performance__{context.run_id.hex}"

    def _download_dataset(
        self,
        *,
        context: PipelineRunContext,
        dataset_key: str,
        dataset_id: str,
        indicators: tuple[str, ...],
    ) -> _DatasetDownload:
        meta_url = DFE_DATASET_META_URL_TEMPLATE.format(dataset_id=dataset_id)
        dataset_url = DFE_DATASET_URL_TEMPLATE.format(dataset_id=dataset_id)
        query_url = DFE_DATASET_QUERY_URL_TEMPLATE.format(dataset_id=dataset_id)

        meta_payload = _download_json(meta_url, timeout_seconds=context.http_timeout_seconds)
        dataset_payload = _download_json(dataset_url, timeout_seconds=context.http_timeout_seconds)
        dataset_version = _extract_dataset_version(dataset_payload)

        meta_file_name = f"{dataset_key}.meta.json"
        meta_path = context.bronze_source_path / meta_file_name
        meta_path.write_text(
            json.dumps(meta_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        assets: list[dict[str, object]] = [
            {
                "bronze_file_name": meta_file_name,
                "source_reference": meta_url,
                "sha256": _sha256_file(meta_path),
                "rows": 0,
            }
        ]

        page = 1
        total_pages = 1
        total_rows = 0
        page_files: list[str] = []
        while page <= total_pages:
            query_payload = {
                "indicators": list(indicators),
                "page": page,
                "pageSize": self._page_size,
            }
            query_response = _post_json(
                query_url,
                payload=query_payload,
                timeout_seconds=context.http_timeout_seconds,
            )

            page_file_name = f"{dataset_key}.page-{page:05d}.json"
            page_path = context.bronze_source_path / page_file_name
            page_path.write_text(
                json.dumps(query_response, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            page_files.append(page_file_name)

            page_results = _as_list(query_response.get("results"))
            page_rows = len(page_results)
            total_rows += page_rows
            assets.append(
                {
                    "bronze_file_name": page_file_name,
                    "source_reference": query_url,
                    "sha256": _sha256_file(page_path),
                    "rows": page_rows,
                    "page": page,
                }
            )

            paging_payload = _as_dict(query_response.get("paging"))
            parsed_total_pages = _parse_int(paging_payload.get("totalPages"))
            if parsed_total_pages is not None and parsed_total_pages > 0:
                total_pages = parsed_total_pages
            else:
                total_pages = page
            page += 1

        return _DatasetDownload(
            dataset_key=dataset_key,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            meta_file_name=meta_file_name,
            page_files=tuple(page_files),
            rows=total_rows,
            assets=tuple(assets),
        )


def _to_staged_row(row: _PerformanceAccumulator) -> DfePerformanceStagedRow:
    return DfePerformanceStagedRow(
        urn=row.urn,
        academic_year=row.academic_year,
        attainment8_average=row.attainment8_average,
        progress8_average=row.progress8_average,
        progress8_disadvantaged=row.progress8_disadvantaged,
        progress8_not_disadvantaged=row.progress8_not_disadvantaged,
        progress8_disadvantaged_gap=_optional_gap(
            row.progress8_disadvantaged,
            row.progress8_not_disadvantaged,
        ),
        engmath_5_plus_pct=row.engmath_5_plus_pct,
        engmath_4_plus_pct=row.engmath_4_plus_pct,
        ebacc_entry_pct=row.ebacc_entry_pct,
        ebacc_5_plus_pct=row.ebacc_5_plus_pct,
        ebacc_4_plus_pct=row.ebacc_4_plus_pct,
        ks2_reading_expected_pct=row.ks2_reading_expected_pct,
        ks2_writing_expected_pct=row.ks2_writing_expected_pct,
        ks2_maths_expected_pct=row.ks2_maths_expected_pct,
        ks2_combined_expected_pct=row.ks2_combined_expected_pct,
        ks2_reading_higher_pct=row.ks2_reading_higher_pct,
        ks2_writing_higher_pct=row.ks2_writing_higher_pct,
        ks2_maths_higher_pct=row.ks2_maths_higher_pct,
        ks2_combined_higher_pct=row.ks2_combined_higher_pct,
        ks2_source_dataset_id=row.ks2_source_dataset_id,
        ks2_source_dataset_version=row.ks2_source_dataset_version,
        ks4_source_dataset_id=row.ks4_source_dataset_id,
        ks4_source_dataset_version=row.ks4_source_dataset_version,
    )


def _optional_gap(first: float | None, second: float | None) -> float | None:
    if first is None or second is None:
        return None
    return first - second


def _parse_ks4_total_values(values: Mapping[str, object]) -> dict[str, float | None]:
    return {
        "attainment8_average": _parse_optional_numeric(
            values.get(performance_contract.KS4_INDICATOR_IDS["attainment8_average"])
        ),
        "progress8_average": _parse_optional_numeric(
            values.get(performance_contract.KS4_INDICATOR_IDS["progress8_average"])
        ),
        "engmath_5_plus_pct": _parse_optional_numeric(
            values.get(performance_contract.KS4_INDICATOR_IDS["engmath_5_plus_pct"])
        ),
        "engmath_4_plus_pct": _parse_optional_numeric(
            values.get(performance_contract.KS4_INDICATOR_IDS["engmath_4_plus_pct"])
        ),
        "ebacc_entry_pct": _parse_optional_numeric(
            values.get(performance_contract.KS4_INDICATOR_IDS["ebacc_entry_pct"])
        ),
        "ebacc_5_plus_pct": _parse_optional_numeric(
            values.get(performance_contract.KS4_INDICATOR_IDS["ebacc_5_plus_pct"])
        ),
        "ebacc_4_plus_pct": _parse_optional_numeric(
            values.get(performance_contract.KS4_INDICATOR_IDS["ebacc_4_plus_pct"])
        ),
    }


def _normalize_result_key(
    result: Mapping[str, object],
    *,
    urn_lookup: Mapping[str, str],
) -> tuple[tuple[str, str] | None, str | None]:
    time_period_payload = _as_dict(result.get("timePeriod"))
    period = _as_str(time_period_payload.get("period"))
    if period is None:
        return None, "missing_time_period"

    with suppress(ValueError):
        academic_year = performance_contract.normalize_academic_year_from_period(period)
        urn = _extract_urn(_as_dict(result.get("locations")), urn_lookup=urn_lookup)
        if urn is None:
            return None, "missing_school_location"
        return (urn, academic_year), None
    return None, "invalid_time_period"


def _extract_urn(
    locations_payload: Mapping[str, object],
    *,
    urn_lookup: Mapping[str, str],
) -> str | None:
    for value in locations_payload.values():
        token = _as_str(value)
        if token is None:
            continue
        if token in urn_lookup:
            token = urn_lookup[token]
        normalized = _normalize_urn(token)
        if normalized is not None:
            return normalized
    return None


def _normalize_urn(value: str) -> str | None:
    token = value.strip()
    if not token or not token.isdigit():
        return None
    if len(token) < 5 or len(token) > 8:
        return None
    return token


def _school_location_urn_lookup(meta_payload: Mapping[str, object]) -> dict[str, str]:
    locations_payload = _as_dict(meta_payload.get("locations"))
    options_payload = _as_list(locations_payload.get("options"))
    lookup: dict[str, str] = {}

    for raw_option in options_payload:
        option = _as_dict(raw_option)
        option_id = _as_str(option.get("id"))
        if option_id is None:
            continue
        code_candidate = (
            _as_str(option.get("code"))
            or _as_str(option.get("value"))
            or _as_str(option.get("label"))
            or option_id
        )
        normalized_urn = _normalize_urn(code_candidate)
        if normalized_urn is None:
            continue
        lookup[option_id] = normalized_urn
    return lookup


def _parse_manifest_datasets(
    manifest_payload: Mapping[str, object],
) -> dict[str, _ManifestDataset]:
    datasets: dict[str, _ManifestDataset] = {}
    for raw_dataset in _as_list(manifest_payload.get("datasets")):
        dataset = _as_dict(raw_dataset)
        dataset_key = _as_str(dataset.get("dataset_key"))
        dataset_id = _as_str(dataset.get("dataset_id"))
        meta_file_name = _as_str(dataset.get("meta_file_name"))
        page_files = tuple(
            page_file
            for page_file in (_as_str(item) for item in _as_list(dataset.get("page_files")))
            if page_file is not None
        )
        if dataset_key is None or dataset_id is None or meta_file_name is None:
            continue
        datasets[dataset_key] = {
            "dataset_id": dataset_id,
            "dataset_version": _as_str(dataset.get("dataset_version")),
            "meta_file_name": meta_file_name,
            "page_files": page_files,
        }
    return datasets


def _select_lookback_years(*, years: tuple[str, ...], lookback_years: int) -> tuple[str, ...]:
    if lookback_years <= 0:
        return ()
    ordered = sorted(set(years), key=lambda value: (_academic_year_sort_key(value), value))
    if len(ordered) <= lookback_years:
        return tuple(ordered)
    return tuple(ordered[-lookback_years:])


def _academic_year_sort_key(value: str) -> int:
    with suppress(ValueError):
        normalized = performance_contract.normalize_academic_year(value)
        return int(normalized[:4])
    return -1


def _parse_optional_numeric(value: object) -> float | None:
    try:
        return performance_contract.parse_optional_number(value)
    except ValueError:
        return None


def _extract_dataset_version(payload: Mapping[str, object]) -> str | None:
    latest_version = _as_dict(payload.get("latestVersion"))
    latest_version_value = _as_str(latest_version.get("version"))
    if latest_version_value is not None:
        return latest_version_value

    versions = _as_list(payload.get("versions"))
    for raw_version in versions:
        parsed_version = _as_dict(raw_version)
        candidate = _as_str(parsed_version.get("version"))
        if candidate is not None:
            return candidate

    return _as_str(payload.get("version"))


def _download_json(url: str, *, timeout_seconds: float) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "civitas-pipeline/0.1"},
    )
    return _request_json(request, timeout_seconds=timeout_seconds)


def _post_json(
    url: str,
    *,
    payload: Mapping[str, object],
    timeout_seconds: float,
) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "civitas-pipeline/0.1",
        },
        method="POST",
    )
    return _request_json(request, timeout_seconds=timeout_seconds)


def _request_json(request: urllib.request.Request, *, timeout_seconds: float) -> dict[str, object]:
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        raw_bytes = response.read()
        payload = json.loads(
            _decode_response_bytes(
                raw_bytes=raw_bytes,
                content_encoding=response.headers.get("Content-Encoding"),
            )
        )
    if isinstance(payload, dict):
        return payload
    raise ValueError("Expected JSON object response from DfE statistics endpoint.")


def _decode_response_bytes(*, raw_bytes: bytes, content_encoding: str | None) -> str:
    encoding_value = (content_encoding or "").casefold()
    should_try_gzip = "gzip" in encoding_value or raw_bytes.startswith(b"\x1f\x8b")
    if should_try_gzip:
        with suppress(OSError):
            raw_bytes = gzip.decompress(raw_bytes)
    return raw_bytes.decode("utf-8-sig", errors="replace")


def _clear_existing_bronze_files(bronze_source_path: Path) -> None:
    for file_path in bronze_source_path.iterdir():
        if file_path.is_file():
            file_path.unlink()


def _manifest_assets_exist(
    manifest_payload: Mapping[str, object],
    *,
    bronze_source_path: Path,
) -> bool:
    assets = _as_list(manifest_payload.get("assets"))
    if not assets:
        return False
    for raw_asset in assets:
        asset = _as_dict(raw_asset)
        file_name = _as_str(asset.get("bronze_file_name"))
        expected_sha = _as_str(asset.get("sha256"))
        if file_name is None:
            return False
        file_path = bronze_source_path / file_name
        if not file_path.exists():
            return False
        if expected_sha is not None and _sha256_file(file_path) != expected_sha:
            return False
    return True


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json_dict(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _parse_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        token = value.strip()
        if not token:
            return None
        with suppress(ValueError):
            return int(float(token))
    return None


def _as_dict(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []


def _as_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    token = value.strip()
    if not token:
        return None
    return token
