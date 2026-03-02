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

from .base import PipelineRunContext, PipelineSource, StageResult

DFE_BASE_URL = "https://api.education.gov.uk/statistics/v1"
DFE_DATASET_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}"
DFE_DATASET_CSV_URL_TEMPLATE = f"{DFE_BASE_URL}/data-sets/{{dataset_id}}/csv"

REQUIRED_DFE_CHARACTERISTICS_HEADERS: tuple[str, ...] = (
    "school_urn",
    "time_period",
    "ptfsm6cla1a",
    "psenelek",
    "psenelk",
    "psenele",
    "ptealgrp2",
    "ptealgrp1",
    "ptealgrp3",
)

NUMERIC_SENTINELS = {"", "SUPP", "NE", "N/A", "NA", "X", "Z", "C"}
BRONZE_FILE_NAME = "school_characteristics.csv"


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


def validate_dfe_characteristics_headers(headers: Sequence[str]) -> None:
    header_set = set(headers)
    missing = [
        header for header in REQUIRED_DFE_CHARACTERISTICS_HEADERS if header not in header_set
    ]
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(f"DfE schema mismatch; missing required headers: {missing_fields}")


def normalize_dfe_characteristics_row(
    raw_row: Mapping[str, str],
    *,
    source_dataset_id: str,
    source_dataset_version: str | None = None,
) -> tuple[DfeCharacteristicsStagedRow | None, str | None]:
    urn = raw_row["school_urn"].strip()
    if not urn:
        return None, "missing_urn"

    try:
        academic_year = _normalize_academic_year(raw_row["time_period"])
    except ValueError:
        return None, "invalid_academic_year"

    try:
        disadvantaged_pct = _parse_optional_percentage(raw_row["ptfsm6cla1a"])
    except ValueError:
        return None, "invalid_disadvantaged_pct"

    try:
        sen_pct = _parse_optional_percentage(raw_row["psenelek"])
    except ValueError:
        return None, "invalid_sen_pct"

    try:
        sen_support_pct = _parse_optional_percentage(raw_row["psenelk"])
    except ValueError:
        return None, "invalid_sen_support_pct"

    try:
        ehcp_pct = _parse_optional_percentage(raw_row["psenele"])
    except ValueError:
        return None, "invalid_ehcp_pct"

    try:
        eal_pct = _parse_optional_percentage(raw_row["ptealgrp2"])
    except ValueError:
        return None, "invalid_eal_pct"

    try:
        first_language_english_pct = _parse_optional_percentage(raw_row["ptealgrp1"])
    except ValueError:
        return None, "invalid_first_language_english_pct"

    try:
        first_language_unclassified_pct = _parse_optional_percentage(raw_row["ptealgrp3"])
    except ValueError:
        return None, "invalid_first_language_unclassified_pct"

    try:
        total_pupils = _parse_total_pupils(raw_row)
    except ValueError:
        return None, "invalid_total_pupils"

    return (
        DfeCharacteristicsStagedRow(
            urn=urn,
            academic_year=academic_year,
            disadvantaged_pct=disadvantaged_pct,
            sen_pct=sen_pct,
            sen_support_pct=sen_support_pct,
            ehcp_pct=ehcp_pct,
            eal_pct=eal_pct,
            first_language_english_pct=first_language_english_pct,
            first_language_unclassified_pct=first_language_unclassified_pct,
            total_pupils=total_pupils,
            source_dataset_id=source_dataset_id,
            source_dataset_version=source_dataset_version,
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
    ) -> None:
        self._engine = engine
        self._source_dataset_id = source_dataset_id
        self._source_csv = source_csv

    def download(self, context: PipelineRunContext) -> int:
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
        source_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if not source_csv.exists():
            raise FileNotFoundError(
                f"DfE bronze file not found at '{source_csv}'. Run download stage first."
            )

        metadata = _load_download_metadata(source_csv.with_suffix(".metadata.json"))
        source_dataset_id = str(metadata.get("source_dataset_id") or self._source_dataset_id)
        source_dataset_version_raw = metadata.get("source_dataset_version")
        source_dataset_version = (
            str(source_dataset_version_raw) if isinstance(source_dataset_version_raw, str) else None
        )

        staged_rows_by_key: dict[tuple[str, str], DfeCharacteristicsStagedRow] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        with source_csv.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise ValueError("DfE characteristics CSV has no header row.")

            validate_dfe_characteristics_headers(reader.fieldnames)

            for raw_row in reader:
                normalized, rejection = normalize_dfe_characteristics_row(
                    raw_row,
                    source_dataset_id=source_dataset_id,
                    source_dataset_version=source_dataset_version,
                )
                if normalized is not None:
                    staged_rows_by_key[(normalized.urn, normalized.academic_year)] = normalized
                    continue
                if rejection is not None:
                    rejected_rows.append((rejection, dict(raw_row)))

        staged_rows = list(staged_rows_by_key.values())

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
                connection.execute(
                    text(
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
                    ),
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
                            "first_language_unclassified_pct": row.first_language_unclassified_pct,
                            "total_pupils": row.total_pupils,
                            "source_dataset_id": row.source_dataset_id,
                            "source_dataset_version": row.source_dataset_version,
                        }
                        for row in staged_rows
                    ],
                )

            if rejected_rows:
                connection.execute(
                    text(
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
                    ),
                    [
                        {
                            "run_id": str(context.run_id),
                            "source": context.source.value,
                            "reason_code": reason_code,
                            "raw_record": json.dumps(raw_row, ensure_ascii=True),
                        }
                        for reason_code, raw_row in rejected_rows
                    ],
                )

        return StageResult(staged_rows=len(staged_rows), rejected_rows=len(rejected_rows))

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


def _fetch_dataset_version(source_dataset_id: str) -> str | None:
    dataset_url = DFE_DATASET_URL_TEMPLATE.format(dataset_id=source_dataset_id)
    request = urllib.request.Request(dataset_url, headers={"User-Agent": "civitas-pipeline/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(
                _decode_response_bytes(response.read(), response.headers.get("Content-Encoding"))
            )
    except Exception:
        return None

    latest_version = payload.get("latestVersion")
    if not isinstance(latest_version, dict):
        return None

    for key in ("id", "version"):
        value = latest_version.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


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
