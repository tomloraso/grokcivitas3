from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import shutil
import urllib.parse
import urllib.request
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import dfe as dfe_contract

DFE_BASE_URL = "https://api.education.gov.uk/statistics/v1"
DFE_DATASET_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}"
DFE_DATASET_CSV_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}/csv"

REQUIRED_DFE_CHARACTERISTICS_HEADERS = dfe_contract.REQUIRED_HEADERS

NUMERIC_SENTINELS = {"", "SUPP", "NE", "N/A", "NA", "X", "Z", "C"}
BRONZE_FILE_NAME = "school_characteristics.csv"
DFE_BACKFILL_MANIFEST_FILE_NAME = "school_characteristics.backfill.manifest.json"
DFE_NORMALIZATION_CONTRACT_VERSION = dfe_contract.CONTRACT_VERSION


@dataclass(frozen=True)
class DfeCharacteristicsStagedRow:
    urn: str
    academic_year: str
    disadvantaged_pct: float | None
    sen_pct: float | None
    sen_support_pct: float | None
    ehcp_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None
    total_pupils: int | None
    source_dataset_id: str
    source_dataset_version: str | None


@dataclass(frozen=True)
class DfeCharacteristicsBackfillSource:
    dataset_id: str
    dataset_version: str | None
    academic_year: str | None


@dataclass(frozen=True)
class DfeCharacteristicsBackfillAsset:
    bronze_file_name: str
    source_reference: str
    source_dataset_id: str
    source_dataset_version: str | None
    source_academic_year: str | None


def validate_dfe_characteristics_headers(headers: Sequence[str]) -> None:
    dfe_contract.validate_headers(tuple(headers))


def normalize_dfe_characteristics_row(
    raw_row: Mapping[str, str],
    *,
    source_dataset_id: str,
    source_dataset_version: str | None = None,
) -> tuple[DfeCharacteristicsStagedRow | None, str | None]:
    normalized_row, rejection = dfe_contract.normalize_row(
        raw_row,
        source_dataset_id=source_dataset_id,
        source_dataset_version=source_dataset_version,
    )
    if normalized_row is None:
        return None, rejection
    return (
        DfeCharacteristicsStagedRow(
            urn=normalized_row["urn"],
            academic_year=normalized_row["academic_year"],
            disadvantaged_pct=normalized_row["disadvantaged_pct"],
            sen_pct=normalized_row["sen_pct"],
            sen_support_pct=normalized_row["sen_support_pct"],
            ehcp_pct=normalized_row["ehcp_pct"],
            eal_pct=normalized_row["eal_pct"],
            first_language_english_pct=normalized_row["first_language_english_pct"],
            first_language_unclassified_pct=normalized_row["first_language_unclassified_pct"],
            total_pupils=normalized_row["total_pupils"],
            source_dataset_id=normalized_row["source_dataset_id"],
            source_dataset_version=normalized_row["source_dataset_version"],
        ),
        None,
    )


class DfeCharacteristicsPipeline:
    source = PipelineSource.DFE_CHARACTERISTICS

    def __init__(
        self,
        engine: Engine,
        source_dataset_id: str,
        source_csv: str | None = None,
        *,
        backfill_enabled: bool = False,
        lookback_years: int = 5,
        source_dataset_catalog: Sequence[str] | None = None,
    ) -> None:
        if lookback_years <= 0:
            raise ValueError("DfE characteristics lookback years must be greater than 0.")

        self._engine = engine
        self._source_dataset_id = source_dataset_id
        self._source_csv = source_csv
        self._backfill_enabled = backfill_enabled
        self._lookback_years = lookback_years
        self._source_dataset_catalog = tuple(source_dataset_catalog or ())

    def download(self, context: PipelineRunContext) -> int:
        if self._backfill_enabled:
            return self._download_backfill(context)

        context.bronze_source_path.mkdir(parents=True, exist_ok=True)

        target_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if target_csv.exists():
            return _count_csv_rows(target_csv)

        source_dataset_version: str | None = None
        if self._source_csv:
            _copy_from_source(self._source_csv, target_csv)
            source_reference = self._source_csv
        else:
            source_reference = DFE_DATASET_CSV_URL_TEMPLATE.format(
                dataset_id=self._source_dataset_id
            )
            csv_text = _download_text(source_reference)
            target_csv.write_text(csv_text, encoding="utf-8")
            source_dataset_version = _fetch_dataset_version(self._source_dataset_id)

        return self._finalize_download_metadata(
            target_csv=target_csv,
            source_reference=source_reference,
            source_dataset_id=self._source_dataset_id,
            source_dataset_version=source_dataset_version,
        )

    def stage(self, context: PipelineRunContext) -> StageResult:
        staged_rows_by_key: dict[tuple[str, str], DfeCharacteristicsStagedRow] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        for source_asset in self._staging_sources(context):
            source_csv = context.bronze_source_path / source_asset.bronze_file_name
            if not source_csv.exists():
                raise FileNotFoundError(
                    f"DfE bronze file not found at '{source_csv}'. Run download stage first."
                )

            with source_csv.open("r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                if reader.fieldnames is None:
                    raise ValueError("DfE characteristics CSV has no header row.")

                validate_dfe_characteristics_headers(reader.fieldnames)

                for raw_row in reader:
                    normalized, rejection = normalize_dfe_characteristics_row(
                        raw_row,
                        source_dataset_id=source_asset.source_dataset_id,
                        source_dataset_version=source_asset.source_dataset_version,
                    )
                    if normalized is not None:
                        staged_rows_by_key[(normalized.urn, normalized.academic_year)] = normalized
                        continue
                    if rejection is not None:
                        rejected_rows.append((rejection, dict(raw_row)))

        staged_rows = list(staged_rows_by_key.values())
        if self._backfill_enabled:
            staged_rows = _filter_rows_to_lookback_years(
                staged_rows,
                lookback_years=self._lookback_years,
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
                        disadvantaged_pct double precision NULL,
                        sen_pct double precision NULL,
                        sen_support_pct double precision NULL,
                        ehcp_pct double precision NULL,
                        eal_pct double precision NULL,
                        first_language_english_pct double precision NULL,
                        first_language_unclassified_pct double precision NULL,
                        total_pupils integer NULL,
                        source_dataset_id text NOT NULL,
                        source_dataset_version text NULL,
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
                        disadvantaged_pct,
                        sen_pct,
                        sen_support_pct,
                        ehcp_pct,
                        eal_pct,
                        first_language_english_pct,
                        first_language_unclassified_pct,
                        total_pupils,
                        source_dataset_id,
                        source_dataset_version
                    ) VALUES (
                        :urn,
                        :academic_year,
                        :disadvantaged_pct,
                        :sen_pct,
                        :sen_support_pct,
                        :ehcp_pct,
                        :eal_pct,
                        :first_language_english_pct,
                        :first_language_unclassified_pct,
                        :total_pupils,
                        :source_dataset_id,
                        :source_dataset_version
                    )
                    ON CONFLICT (urn, academic_year) DO UPDATE SET
                        disadvantaged_pct = EXCLUDED.disadvantaged_pct,
                        sen_pct = EXCLUDED.sen_pct,
                        sen_support_pct = EXCLUDED.sen_support_pct,
                        ehcp_pct = EXCLUDED.ehcp_pct,
                        eal_pct = EXCLUDED.eal_pct,
                        first_language_english_pct = EXCLUDED.first_language_english_pct,
                        first_language_unclassified_pct = EXCLUDED.first_language_unclassified_pct,
                        total_pupils = EXCLUDED.total_pupils,
                        source_dataset_id = EXCLUDED.source_dataset_id,
                        source_dataset_version = EXCLUDED.source_dataset_version
                    """
                )
                for rows_chunk in chunked(staged_rows, context.stage_chunk_size):
                    connection.execute(
                        staged_insert,
                        [
                            {
                                "urn": row.urn,
                                "academic_year": row.academic_year,
                                "disadvantaged_pct": row.disadvantaged_pct,
                                "sen_pct": row.sen_pct,
                                "sen_support_pct": row.sen_support_pct,
                                "ehcp_pct": row.ehcp_pct,
                                "eal_pct": row.eal_pct,
                                "first_language_english_pct": row.first_language_english_pct,
                                "first_language_unclassified_pct": (
                                    row.first_language_unclassified_pct
                                ),
                                "total_pupils": row.total_pupils,
                                "source_dataset_id": row.source_dataset_id,
                                "source_dataset_version": row.source_dataset_version,
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
            contract_version=DFE_NORMALIZATION_CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            promoted_rows = int(
                connection.execute(
                    text(
                        f"""
                        WITH upserted AS (
                            INSERT INTO school_demographics_yearly (
                                urn,
                                academic_year,
                                disadvantaged_pct,
                                fsm_pct,
                                sen_pct,
                                sen_support_pct,
                                ehcp_pct,
                                eal_pct,
                                first_language_english_pct,
                                first_language_unclassified_pct,
                                total_pupils,
                                has_ethnicity_data,
                                has_top_languages_data,
                                source_dataset_id,
                                source_dataset_version,
                                updated_at
                            )
                            SELECT
                                staged.urn,
                                staged.academic_year,
                                staged.disadvantaged_pct,
                                NULL,
                                staged.sen_pct,
                                staged.sen_support_pct,
                                staged.ehcp_pct,
                                staged.eal_pct,
                                staged.first_language_english_pct,
                                staged.first_language_unclassified_pct,
                                staged.total_pupils,
                                FALSE,
                                FALSE,
                                staged.source_dataset_id,
                                staged.source_dataset_version,
                                timezone('utc', now())
                            FROM staging.{staging_table_name} AS staged
                            INNER JOIN schools ON schools.urn = staged.urn
                            ON CONFLICT (urn, academic_year) DO UPDATE SET
                                disadvantaged_pct = EXCLUDED.disadvantaged_pct,
                                fsm_pct = EXCLUDED.fsm_pct,
                                sen_pct = EXCLUDED.sen_pct,
                                sen_support_pct = EXCLUDED.sen_support_pct,
                                ehcp_pct = EXCLUDED.ehcp_pct,
                                eal_pct = EXCLUDED.eal_pct,
                                first_language_english_pct = EXCLUDED.first_language_english_pct,
                                first_language_unclassified_pct = EXCLUDED.first_language_unclassified_pct,
                                total_pupils = EXCLUDED.total_pupils,
                                has_ethnicity_data = EXCLUDED.has_ethnicity_data,
                                has_top_languages_data = EXCLUDED.has_top_languages_data,
                                source_dataset_id = EXCLUDED.source_dataset_id,
                                source_dataset_version = EXCLUDED.source_dataset_version,
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
        return f"dfe_characteristics__{context.run_id.hex}"

    def _download_backfill(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        manifest_path = context.bronze_source_path / DFE_BACKFILL_MANIFEST_FILE_NAME

        existing_assets = _manifest_backfill_assets(_load_download_metadata(manifest_path))
        if existing_assets and all(
            (context.bronze_source_path / asset.bronze_file_name).exists()
            for asset in existing_assets
        ):
            return sum(
                _count_csv_rows(context.bronze_source_path / asset.bronze_file_name)
                for asset in existing_assets
            )

        backfill_sources = self._resolve_backfill_sources()
        if not backfill_sources:
            return 0

        manifest_assets: list[dict[str, object]] = []
        total_rows = 0
        for index, source in enumerate(backfill_sources, start=1):
            source_reference = DFE_DATASET_CSV_URL_TEMPLATE.format(dataset_id=source.dataset_id)
            bronze_file_name = _build_backfill_file_name(source, index=index)
            target_csv = context.bronze_source_path / bronze_file_name
            target_csv.write_text(_download_text(source_reference), encoding="utf-8")

            row_count = _count_csv_rows(target_csv)
            total_rows += row_count
            manifest_assets.append(
                {
                    "bronze_file_name": bronze_file_name,
                    "source_reference": source_reference,
                    "source_dataset_id": source.dataset_id,
                    "source_dataset_version": source.dataset_version,
                    "source_academic_year": source.academic_year,
                    "sha256": _sha256_file(target_csv),
                    "rows": row_count,
                }
            )

        manifest_payload = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "normalization_contract_version": DFE_NORMALIZATION_CONTRACT_VERSION,
            "lookback_years": self._lookback_years,
            "assets": manifest_assets,
        }
        manifest_path.write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return total_rows

    def _resolve_backfill_sources(self) -> tuple[DfeCharacteristicsBackfillSource, ...]:
        dataset_ids = (
            tuple(self._source_dataset_catalog)
            if self._source_dataset_catalog
            else (self._source_dataset_id,)
        )

        sources: list[DfeCharacteristicsBackfillSource] = []
        for dataset_id in dataset_ids:
            summary = _fetch_dataset_summary(dataset_id)
            latest_version = summary.get("latestVersion")
            if not isinstance(latest_version, dict):
                latest_version = {}

            sources.append(
                DfeCharacteristicsBackfillSource(
                    dataset_id=dataset_id,
                    dataset_version=_extract_dataset_version(latest_version),
                    academic_year=_extract_dataset_academic_year(latest_version),
                )
            )

        by_year: dict[str, DfeCharacteristicsBackfillSource] = {}
        sources_without_year: list[DfeCharacteristicsBackfillSource] = []
        for source in sources:
            if source.academic_year is None:
                sources_without_year.append(source)
                continue
            by_year[source.academic_year] = source

        if by_year:
            ranked = sorted(
                by_year.values(),
                key=lambda source: _academic_year_sort_key(source.academic_year),
            )
            return tuple(ranked[-self._lookback_years :])

        return tuple(sources_without_year[-self._lookback_years :])

    def _staging_sources(
        self, context: PipelineRunContext
    ) -> tuple[DfeCharacteristicsBackfillAsset, ...]:
        if self._backfill_enabled:
            manifest_path = context.bronze_source_path / DFE_BACKFILL_MANIFEST_FILE_NAME
            assets = _manifest_backfill_assets(_load_download_metadata(manifest_path))
            if not assets:
                raise ValueError(
                    "DfE backfill manifest missing assets. Run download stage before stage."
                )
            return tuple(
                sorted(
                    assets,
                    key=lambda asset: (
                        _academic_year_sort_key(asset.source_academic_year),
                        asset.source_dataset_id,
                        asset.bronze_file_name,
                    ),
                )
            )

        source_csv = context.bronze_source_path / BRONZE_FILE_NAME
        metadata = _load_download_metadata(source_csv.with_suffix(".metadata.json"))
        source_dataset_id = str(metadata.get("source_dataset_id") or self._source_dataset_id)
        source_dataset_version_raw = metadata.get("source_dataset_version")
        source_dataset_version = (
            str(source_dataset_version_raw) if isinstance(source_dataset_version_raw, str) else None
        )
        source_academic_year_raw = metadata.get("source_academic_year")
        source_academic_year = (
            str(source_academic_year_raw).strip()
            if isinstance(source_academic_year_raw, str) and source_academic_year_raw.strip()
            else None
        )
        return (
            DfeCharacteristicsBackfillAsset(
                bronze_file_name=BRONZE_FILE_NAME,
                source_reference=str(metadata.get("source_reference") or BRONZE_FILE_NAME),
                source_dataset_id=source_dataset_id,
                source_dataset_version=source_dataset_version,
                source_academic_year=source_academic_year,
            ),
        )

    def _finalize_download_metadata(
        self,
        *,
        target_csv: Path,
        source_reference: str,
        source_dataset_id: str,
        source_dataset_version: str | None,
    ) -> int:
        row_count = _count_csv_rows(target_csv)
        metadata_path = target_csv.with_suffix(".metadata.json")
        metadata = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "source_reference": source_reference,
            "source_dataset_id": source_dataset_id,
            "source_dataset_version": source_dataset_version,
            "normalization_contract_version": DFE_NORMALIZATION_CONTRACT_VERSION,
            "sha256": _sha256_file(target_csv),
            "rows": row_count,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        return row_count


def _normalize_academic_year(raw_value: str | None) -> str:
    value = (raw_value or "").strip()
    if len(value) == 7 and value[4] == "/" and value[:4].isdigit() and value[5:].isdigit():
        return value
    raise ValueError("invalid academic year")


def _parse_optional_percentage(raw_value: str | None) -> float | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    if value.upper() in NUMERIC_SENTINELS:
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError("invalid numeric value") from exc

    if not math.isfinite(parsed):
        raise ValueError("numeric value must be finite")
    if parsed < 0.0 or parsed > 100.0:
        raise ValueError("percentage out of range")

    return parsed


def _parse_total_pupils(raw_row: Mapping[str, str]) -> int | None:
    for field_name in ("total_pupils", "number_of_pupils"):
        raw_value = raw_row.get(field_name)
        if raw_value is None:
            continue
        value = raw_value.strip()
        if not value:
            return None
        if value.upper() in NUMERIC_SENTINELS:
            return None
        try:
            return int(float(value))
        except ValueError as exc:
            raise ValueError("invalid_total_pupils") from exc
    return None


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        row_count_with_header = sum(1 for _ in csv.reader(csv_file))
    return max(0, row_count_with_header - 1)


def _decode_response_bytes(raw_bytes: bytes, content_encoding: str | None) -> str:
    encoding_value = (content_encoding or "").casefold()
    should_try_gzip = "gzip" in encoding_value or raw_bytes.startswith(b"\x1f\x8b")
    if should_try_gzip:
        with suppress(OSError):
            raw_bytes = gzip.decompress(raw_bytes)
    return raw_bytes.decode("utf-8-sig", errors="replace")


def _download_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "civitas-pipeline/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw_bytes = response.read()
        return _decode_response_bytes(raw_bytes, response.headers.get("Content-Encoding"))


def _fetch_dataset_summary(source_dataset_id: str) -> dict[str, object]:
    dataset_url = DFE_DATASET_URL_TEMPLATE.format(dataset_id=source_dataset_id)
    request = urllib.request.Request(dataset_url, headers={"User-Agent": "civitas-pipeline/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(
                _decode_response_bytes(response.read(), response.headers.get("Content-Encoding"))
            )
    except Exception:
        return {}

    if isinstance(payload, dict):
        return payload
    return {}


def _fetch_dataset_version(source_dataset_id: str) -> str | None:
    payload = _fetch_dataset_summary(source_dataset_id)
    latest_version = payload.get("latestVersion")
    if not isinstance(latest_version, dict):
        return None
    return _extract_dataset_version(latest_version)


def _extract_dataset_version(latest_version: Mapping[str, object]) -> str | None:
    for key in ("id", "version"):
        value = latest_version.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_dataset_academic_year(latest_version: Mapping[str, object]) -> str | None:
    time_periods = latest_version.get("timePeriods")
    if not isinstance(time_periods, dict):
        return None
    end_value = time_periods.get("end")
    if not isinstance(end_value, str):
        return None
    with suppress(ValueError):
        return dfe_contract.normalize_academic_year(end_value)
    return None


def _build_backfill_file_name(source: DfeCharacteristicsBackfillSource, *, index: int) -> str:
    academic_year_token = (source.academic_year or "unknown").replace("/", "_")
    return f"{index:02d}_school_characteristics_{academic_year_token}_{source.dataset_id}.csv"


def _academic_year_sort_key(academic_year: str | None) -> tuple[int, str]:
    if academic_year is None:
        return (0, "")
    with suppress(ValueError):
        normalized = dfe_contract.normalize_academic_year(academic_year)
        return (int(normalized[:4]), normalized)
    return (0, academic_year)


def _filter_rows_to_lookback_years(
    rows: Sequence[DfeCharacteristicsStagedRow],
    *,
    lookback_years: int,
) -> list[DfeCharacteristicsStagedRow]:
    if lookback_years <= 0:
        return []
    if len(rows) <= 1:
        return list(rows)

    available_years = sorted(
        {row.academic_year for row in rows},
        key=_academic_year_sort_key,
    )
    selected_years = set(available_years[-lookback_years:])
    return [row for row in rows if row.academic_year in selected_years]


def _manifest_backfill_assets(manifest: dict[str, object]) -> list[DfeCharacteristicsBackfillAsset]:
    assets_payload = manifest.get("assets")
    if not isinstance(assets_payload, list):
        return []

    assets: list[DfeCharacteristicsBackfillAsset] = []
    for payload in assets_payload:
        if not isinstance(payload, dict):
            continue
        bronze_file_name = payload.get("bronze_file_name")
        source_dataset_id = payload.get("source_dataset_id")
        if not isinstance(bronze_file_name, str) or not bronze_file_name.strip():
            continue
        if not isinstance(source_dataset_id, str) or not source_dataset_id.strip():
            continue

        source_reference_value = payload.get("source_reference")
        source_reference = (
            source_reference_value.strip()
            if isinstance(source_reference_value, str) and source_reference_value.strip()
            else bronze_file_name.strip()
        )

        source_dataset_version_value = payload.get("source_dataset_version")
        source_dataset_version = (
            source_dataset_version_value.strip()
            if isinstance(source_dataset_version_value, str)
            and source_dataset_version_value.strip()
            else None
        )

        source_academic_year_value = payload.get("source_academic_year")
        source_academic_year = (
            source_academic_year_value.strip()
            if isinstance(source_academic_year_value, str) and source_academic_year_value.strip()
            else None
        )

        assets.append(
            DfeCharacteristicsBackfillAsset(
                bronze_file_name=bronze_file_name.strip(),
                source_reference=source_reference,
                source_dataset_id=source_dataset_id.strip(),
                source_dataset_version=source_dataset_version,
                source_academic_year=source_academic_year,
            )
        )
    return assets


def _copy_from_source(source: str, target: Path) -> None:
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        request = urllib.request.Request(source, headers={"User-Agent": "civitas-pipeline/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response:
            raw_bytes = response.read()
            text_content = _decode_response_bytes(
                raw_bytes, response.headers.get("Content-Encoding")
            )
            target.write_text(text_content, encoding="utf-8")
        return

    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"Configured DfE source CSV path '{source_path}' was not found.")
    shutil.copy2(source_path, target)


def _load_download_metadata(metadata_path: Path) -> dict[str, object]:
    if not metadata_path.exists():
        return {}
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
