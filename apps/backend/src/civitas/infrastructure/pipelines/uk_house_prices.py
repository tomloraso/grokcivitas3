from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import uk_house_prices as house_price_contract

HOUSE_PRICE_FILE_URL_TEMPLATE = (
    "https://publicdata.landregistry.gov.uk/market-trend-data/"
    "house-price-index-data/Average-prices-{year:04d}-{month:02d}.csv"
)

BRONZE_FILE_NAME = "average_prices.csv"
BRONZE_METADATA_FILE_NAME = "average_prices.metadata.json"
UK_HOUSE_PRICE_NORMALIZATION_CONTRACT_VERSION = house_price_contract.CONTRACT_VERSION
_SOURCE_MONTH_PATTERN = re.compile(r"Average-prices-(\d{4}-\d{2})\.csv$")


@dataclass(frozen=True)
class UkHousePriceStagedRow:
    month: datetime
    area_name: str
    area_code: str
    average_price: float
    monthly_change_pct: float | None
    annual_change_pct: float | None


class UkHousePricesPipeline:
    source = PipelineSource.UK_HOUSE_PRICES

    def __init__(
        self,
        engine: Engine,
        *,
        source_csv: str | None = None,
        source_url: str | None = None,
        max_probe_months: int = 36,
    ) -> None:
        self._engine = engine
        self._source_csv = source_csv
        self._source_url = source_url
        self._max_probe_months = max_probe_months

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)

        target_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if target_csv.exists():
            return _count_csv_rows(target_csv)

        source_file_url: str
        source_month: str | None
        if self._source_csv is not None:
            _copy_from_source(self._source_csv, target_csv)
            source_file_url = self._source_csv
            source_month = _source_month_from_url(self._source_csv)
        else:
            source_file_url = self._source_url or _resolve_latest_source_url(
                max_probe_months=self._max_probe_months
            )
            source_month = _source_month_from_url(source_file_url)
            target_csv.write_text(_download_text(source_file_url), encoding="utf-8")

        row_count = _count_csv_rows(target_csv)
        metadata = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "source_file_url": source_file_url,
            "source_month": source_month,
            "normalization_contract_version": UK_HOUSE_PRICE_NORMALIZATION_CONTRACT_VERSION,
            "sha256": _sha256_file(target_csv),
            "rows": row_count,
        }
        metadata_path = context.bronze_source_path / BRONZE_METADATA_FILE_NAME
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        return row_count

    def stage(self, context: PipelineRunContext) -> StageResult:
        source_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if not source_csv.exists():
            raise FileNotFoundError(
                f"UK house-price bronze file not found at '{source_csv}'. Run download stage first."
            )

        metadata = _load_download_metadata(context.bronze_source_path / BRONZE_METADATA_FILE_NAME)
        source_file_url = (
            str(metadata.get("source_file_url"))
            if isinstance(metadata.get("source_file_url"), str)
            else ""
        )
        source_month = (
            str(metadata.get("source_month"))
            if isinstance(metadata.get("source_month"), str)
            else _source_month_from_url(source_file_url)
        )

        staged_rows_by_key: dict[tuple[str, datetime], UkHousePriceStagedRow] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        with source_csv.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise ValueError("UK house-price CSV has no header row.")
            house_price_contract.validate_headers(reader.fieldnames)

            for raw_row in reader:
                normalized, rejection = house_price_contract.normalize_row(raw_row)
                if normalized is not None:
                    normalized_month = datetime(
                        normalized["month"].year,
                        normalized["month"].month,
                        normalized["month"].day,
                        tzinfo=timezone.utc,
                    )
                    key = (normalized["area_code"], normalized_month)
                    staged_rows_by_key[key] = UkHousePriceStagedRow(
                        month=normalized_month,
                        area_name=normalized["area_name"],
                        area_code=normalized["area_code"],
                        average_price=normalized["average_price"],
                        monthly_change_pct=normalized["monthly_change_pct"],
                        annual_change_pct=normalized["annual_change_pct"],
                    )
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
                        area_code text NOT NULL,
                        area_name text NOT NULL,
                        month date NOT NULL,
                        average_price double precision NOT NULL,
                        monthly_change_pct double precision NULL,
                        annual_change_pct double precision NULL,
                        PRIMARY KEY (area_code, month)
                    )
                    """
                )
            )

            if staged_rows:
                staged_insert = text(
                    f"""
                    INSERT INTO staging.{staging_table_name} (
                        area_code,
                        area_name,
                        month,
                        average_price,
                        monthly_change_pct,
                        annual_change_pct
                    ) VALUES (
                        :area_code,
                        :area_name,
                        :month,
                        :average_price,
                        :monthly_change_pct,
                        :annual_change_pct
                    )
                    ON CONFLICT (area_code, month) DO UPDATE SET
                        area_name = EXCLUDED.area_name,
                        average_price = EXCLUDED.average_price,
                        monthly_change_pct = EXCLUDED.monthly_change_pct,
                        annual_change_pct = EXCLUDED.annual_change_pct
                    """
                )
                for rows_chunk in chunked(staged_rows, context.stage_chunk_size):
                    connection.execute(
                        staged_insert,
                        [
                            {
                                "area_code": row.area_code,
                                "area_name": row.area_name,
                                "month": row.month.date(),
                                "average_price": row.average_price,
                                "monthly_change_pct": row.monthly_change_pct,
                                "annual_change_pct": row.annual_change_pct,
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

        contract_version = UK_HOUSE_PRICE_NORMALIZATION_CONTRACT_VERSION
        if source_month is not None:
            contract_version = f"{contract_version}+{source_month}"
        return StageResult(
            staged_rows=len(staged_rows),
            rejected_rows=len(rejected_rows),
            contract_version=contract_version,
        )

    def promote(self, context: PipelineRunContext) -> int:
        staging_table_name = self._staging_table_name(context)
        metadata = _load_download_metadata(context.bronze_source_path / BRONZE_METADATA_FILE_NAME)
        source_file_url = (
            str(metadata.get("source_file_url"))
            if isinstance(metadata.get("source_file_url"), str)
            else ""
        )
        source_month = (
            str(metadata.get("source_month"))
            if isinstance(metadata.get("source_month"), str)
            else _source_month_from_url(source_file_url)
        )
        source_dataset_version = source_month

        with self._engine.begin() as connection:
            promoted_rows = int(
                connection.execute(
                    text(
                        f"""
                        WITH upserted AS (
                            INSERT INTO area_house_price_context (
                                area_code,
                                area_name,
                                month,
                                average_price,
                                monthly_change_pct,
                                annual_change_pct,
                                source_dataset_id,
                                source_dataset_version,
                                source_file_url,
                                updated_at
                            )
                            SELECT
                                staged.area_code,
                                staged.area_name,
                                staged.month,
                                staged.average_price,
                                staged.monthly_change_pct,
                                staged.annual_change_pct,
                                'uk_hpi_average_price',
                                :source_dataset_version,
                                :source_file_url,
                                timezone('utc', now())
                            FROM staging.{staging_table_name} AS staged
                            ON CONFLICT (area_code, month) DO UPDATE SET
                                area_name = EXCLUDED.area_name,
                                average_price = EXCLUDED.average_price,
                                monthly_change_pct = EXCLUDED.monthly_change_pct,
                                annual_change_pct = EXCLUDED.annual_change_pct,
                                source_dataset_id = EXCLUDED.source_dataset_id,
                                source_dataset_version = EXCLUDED.source_dataset_version,
                                source_file_url = EXCLUDED.source_file_url,
                                updated_at = timezone('utc', now())
                            RETURNING 1
                        )
                        SELECT COUNT(*) FROM upserted
                        """
                    ),
                    {
                        "source_dataset_version": source_dataset_version,
                        "source_file_url": source_file_url,
                    },
                ).scalar_one()
            )
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
        return promoted_rows

    @staticmethod
    def _staging_table_name(context: PipelineRunContext) -> str:
        return f"uk_house_prices__{context.run_id.hex}"


def _resolve_latest_source_url(*, max_probe_months: int) -> str:
    if max_probe_months <= 0:
        raise ValueError("max_probe_months must be greater than 0.")
    today = datetime.now(timezone.utc).date()
    probe_year = today.year
    probe_month = today.month
    for _ in range(max_probe_months):
        candidate_url = HOUSE_PRICE_FILE_URL_TEMPLATE.format(year=probe_year, month=probe_month)
        request = urllib.request.Request(
            candidate_url,
            headers={"User-Agent": "civitas-pipeline/0.1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status == 200:
                    return candidate_url
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
        probe_year, probe_month = _previous_month(probe_year, probe_month)

    raise FileNotFoundError(
        "Unable to resolve a UK house-price source file. "
        f"Checked the latest {max_probe_months} monthly candidates."
    )


def _previous_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _source_month_from_url(url: str) -> str | None:
    match = _SOURCE_MONTH_PATTERN.search(url)
    if match is None:
        return None
    return match.group(1)


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


def _copy_from_source(source: str, target: Path) -> None:
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        target.write_text(_download_text(source), encoding="utf-8")
        return

    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(
            f"Configured UK house-price source CSV path '{source_path}' was not found."
        )
    shutil.copy2(source_path, target)


def _load_download_metadata(metadata_path: Path) -> dict[str, object]:
    if not metadata_path.exists():
        return {}
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
