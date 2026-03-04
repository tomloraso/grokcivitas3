from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import gias as gias_contract

REQUIRED_GIAS_HEADERS = gias_contract.REQUIRED_HEADERS

NUMERIC_SENTINELS = {"", "SUPP", "NE", "N/A", "NA", "X"}
EASTING_RANGE = (0.0, 700000.0)
NORTHING_RANGE = (0.0, 1300000.0)
BRONZE_FILE_NAME = "edubasealldata.csv"
CSV_NAME_SUBSTRING = "edubasealldata"

# GIAS bulk extracts from get-information-schools.service.gov.uk are
# encoded as Windows-1252 (cp1252).  School names frequently contain
# Windows-style right single quotes (\x92) and other characters outside
# the ASCII/UTF-8 range.  cp1252 is a strict superset of ASCII so test
# fixtures authored in plain ASCII are decoded correctly.
GIAS_CSV_ENCODING = "cp1252"
GIAS_NORMALIZATION_CONTRACT_VERSION = gias_contract.CONTRACT_VERSION


@dataclass(frozen=True)
class GiasStagedRow:
    urn: str
    name: str
    phase: str | None
    school_type: str | None
    status: str | None
    postcode: str | None
    easting: float
    northing: float
    open_date: date | None
    close_date: date | None
    pupil_count: int | None
    capacity: int | None


def normalize_gias_postcode(raw_postcode: str | None) -> str | None:
    return gias_contract.normalize_postcode(raw_postcode)


def validate_gias_headers(headers: Sequence[str]) -> None:
    gias_contract.validate_headers(headers)


def normalize_gias_row(raw_row: Mapping[str, str]) -> tuple[GiasStagedRow | None, str | None]:
    normalized_row, rejection = gias_contract.normalize_row(raw_row)
    if normalized_row is None:
        return None, rejection
    return (
        GiasStagedRow(
            urn=normalized_row["urn"],
            name=normalized_row["name"],
            phase=normalized_row["phase"],
            school_type=normalized_row["school_type"],
            status=normalized_row["status"],
            postcode=normalized_row["postcode"],
            easting=normalized_row["easting"],
            northing=normalized_row["northing"],
            open_date=normalized_row["open_date"],
            close_date=normalized_row["close_date"],
            pupil_count=normalized_row["pupil_count"],
            capacity=normalized_row["capacity"],
        ),
        None,
    )


class GiasPipeline:
    source = PipelineSource.GIAS

    def __init__(
        self,
        engine: Engine,
        source_csv: str | None = None,
        source_zip: str | None = None,
    ) -> None:
        self._engine = engine
        self._source_csv = source_csv
        self._source_zip = source_zip

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)

        target_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if target_csv.exists():
            return _count_csv_rows(target_csv)

        if self._source_csv:
            _copy_from_source(self._source_csv, target_csv)
            return self._finalize_download_metadata(target_csv, self._source_csv)

        if self._source_zip:
            _extract_csv_from_zip_source(self._source_zip, target_csv)
            return self._finalize_download_metadata(target_csv, self._source_zip)

        raise RuntimeError(
            "Unable to download GIAS source automatically. Set CIVITAS_GIAS_SOURCE_CSV "
            "or CIVITAS_GIAS_SOURCE_ZIP to a local path or URL."
        )

    def stage(self, context: PipelineRunContext) -> StageResult:
        source_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if not source_csv.exists():
            raise FileNotFoundError(
                f"GIAS bronze file not found at '{source_csv}'. Run download stage first."
            )

        staged_rows: list[GiasStagedRow] = []
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        with source_csv.open("r", encoding=GIAS_CSV_ENCODING, newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise ValueError("GIAS CSV has no header row.")

            validate_gias_headers(reader.fieldnames)

            for raw_row in reader:
                normalized, rejection = normalize_gias_row(raw_row)
                if normalized is not None:
                    staged_rows.append(normalized)
                    continue
                if rejection is not None:
                    rejected_rows.append((rejection, dict(raw_row)))

        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
            connection.execute(
                text(
                    f"""
                    CREATE TABLE staging.{staging_table_name} (
                        urn text PRIMARY KEY,
                        name text NOT NULL,
                        phase text NULL,
                        type text NULL,
                        status text NULL,
                        postcode text NULL,
                        easting double precision NOT NULL,
                        northing double precision NOT NULL,
                        open_date date NULL,
                        close_date date NULL,
                        pupil_count integer NULL,
                        capacity integer NULL
                    )
                    """
                )
            )

            if staged_rows:
                staged_insert = text(
                    f"""
                    INSERT INTO staging.{staging_table_name} (
                        urn,
                        name,
                        phase,
                        type,
                        status,
                        postcode,
                        easting,
                        northing,
                        open_date,
                        close_date,
                        pupil_count,
                        capacity
                    ) VALUES (
                        :urn,
                        :name,
                        :phase,
                        :type,
                        :status,
                        :postcode,
                        :easting,
                        :northing,
                        :open_date,
                        :close_date,
                        :pupil_count,
                        :capacity
                    )
                    """
                )
                for rows_chunk in chunked(staged_rows, context.stage_chunk_size):
                    connection.execute(
                        staged_insert,
                        [
                            {
                                "urn": row.urn,
                                "name": row.name,
                                "phase": row.phase,
                                "type": row.school_type,
                                "status": row.status,
                                "postcode": row.postcode,
                                "easting": row.easting,
                                "northing": row.northing,
                                "open_date": row.open_date,
                                "close_date": row.close_date,
                                "pupil_count": row.pupil_count,
                                "capacity": row.capacity,
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
            contract_version=GIAS_NORMALIZATION_CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            promoted_rows = int(
                connection.execute(
                    text(
                        f"""
                        WITH upserted AS (
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
                                close_date,
                                updated_at
                            )
                            SELECT
                                urn,
                                name,
                                phase,
                                type,
                                status,
                                postcode,
                                easting,
                                northing,
                                ST_Transform(
                                    ST_SetSRID(ST_MakePoint(easting, northing), 27700),
                                    4326
                                )::geography(Point, 4326),
                                capacity,
                                pupil_count,
                                open_date,
                                close_date,
                                timezone('utc', now())
                            FROM staging.{staging_table_name}
                            ON CONFLICT (urn) DO UPDATE SET
                                name = EXCLUDED.name,
                                phase = EXCLUDED.phase,
                                type = EXCLUDED.type,
                                status = EXCLUDED.status,
                                postcode = EXCLUDED.postcode,
                                easting = EXCLUDED.easting,
                                northing = EXCLUDED.northing,
                                location = EXCLUDED.location,
                                capacity = EXCLUDED.capacity,
                                pupil_count = EXCLUDED.pupil_count,
                                open_date = EXCLUDED.open_date,
                                close_date = EXCLUDED.close_date,
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
        return f"gias_schools__{context.run_id.hex}"

    def _finalize_download_metadata(self, target_csv: Path, source_reference: str) -> int:
        row_count = _count_csv_rows(target_csv)
        metadata_path = target_csv.with_suffix(".metadata.json")
        metadata = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "source_reference": source_reference,
            "normalization_contract_version": GIAS_NORMALIZATION_CONTRACT_VERSION,
            "sha256": _sha256_file(target_csv),
            "rows": row_count,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        return row_count


def _is_coordinate_in_range(easting: float, northing: float) -> bool:
    return (
        EASTING_RANGE[0] <= easting <= EASTING_RANGE[1]
        and NORTHING_RANGE[0] <= northing <= NORTHING_RANGE[1]
    )


def _parse_optional_integer(raw_value: str | None) -> int | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value or value.upper() in NUMERIC_SENTINELS:
        return None
    try:
        return int(float(value))
    except ValueError as exc:
        raise ValueError("invalid integer value") from exc


def _parse_optional_date(raw_value: str | None) -> date | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None

    supported_formats = (
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
    )
    for date_format in supported_formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"unsupported date value '{value}'")


def _strip_or_none(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding=GIAS_CSV_ENCODING, newline="") as csv_file:
        row_count_with_header = sum(1 for _ in csv.reader(csv_file))
    return max(0, row_count_with_header - 1)


def _copy_from_source(source: str, target: Path) -> None:
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        request = urllib.request.Request(source, headers={"User-Agent": "civitas-pipeline/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response:
            target.write_bytes(response.read())
        return

    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"Configured source CSV path '{source_path}' was not found.")
    shutil.copy2(source_path, target)


def _extract_csv_from_zip_source(source: str, target_csv: Path) -> None:
    parsed = urllib.parse.urlparse(source)
    zip_path: Path | None = None

    if parsed.scheme in {"http", "https"}:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
            temp_zip_path = Path(temp_zip.name)

        try:
            request = urllib.request.Request(source, headers={"User-Agent": "civitas-pipeline/0.1"})
            with urllib.request.urlopen(request, timeout=60) as response:
                temp_zip_path.write_bytes(response.read())
            zip_path = temp_zip_path
            _extract_matching_csv(zip_path, target_csv)
        finally:
            if temp_zip_path.exists():
                temp_zip_path.unlink()
        return

    zip_path = Path(source)
    if not zip_path.exists():
        raise FileNotFoundError(f"Configured source ZIP path '{zip_path}' was not found.")
    _extract_matching_csv(zip_path, target_csv)


def _extract_matching_csv(zip_path: Path, target_csv: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as archive:
        csv_names = [
            item
            for item in archive.namelist()
            if item.lower().endswith(".csv") and CSV_NAME_SUBSTRING in item.lower()
        ]
        if not csv_names:
            raise ValueError(
                f"No CSV matching '{CSV_NAME_SUBSTRING}' was found in archive '{zip_path}'."
            )

        selected_csv = csv_names[0]
        with archive.open(selected_csv, "r") as source_file:
            target_csv.write_bytes(source_file.read())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
