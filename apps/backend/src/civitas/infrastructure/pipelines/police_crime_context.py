from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import shutil
import urllib.parse
import urllib.request
import zipfile
from contextlib import suppress
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult

POLICE_ARCHIVE_INDEX_URL = "https://data.police.uk/data/archive/"
DEFAULT_POLICE_CRIME_RADIUS_METERS = 1609.344
DEFAULT_POLICE_CRIME_SOURCE_MODE = "archive"
SUPPORTED_POLICE_CRIME_SOURCE_MODES = ("archive", "api")

REQUIRED_POLICE_STREET_HEADERS: tuple[str, ...] = (
    "Crime type",
    "Longitude",
    "Latitude",
    "Month",
)

BRONZE_ARCHIVE_FILE_NAME = "archive.zip"
BRONZE_METADATA_FILE_NAME = "archive.metadata.json"
BRONZE_EXTRACTED_DIR = "extracted"


@dataclass(frozen=True)
class PoliceCrimePoint:
    month: date
    crime_category: str
    longitude: float
    latitude: float


def extract_latest_police_archive_url(index_html: str) -> str:
    archive_links: dict[str, str] = {}
    marker = "/data/archive/"
    suffix = ".zip"
    start = 0
    while True:
        position = index_html.find(marker, start)
        if position == -1:
            break
        month = index_html[position + len(marker) : position + len(marker) + 7]
        if len(month) == 7 and month[4] == "-" and month[:4].isdigit() and month[5:].isdigit():
            candidate = f"https://data.police.uk{marker}{month}{suffix}"
            archive_links[month] = candidate
        start = position + len(marker)

    if not archive_links:
        raise ValueError("Unable to resolve Police archive URL from index page.")

    latest_month = max(archive_links.keys())
    return archive_links[latest_month]


def validate_police_street_headers(headers: Sequence[str]) -> None:
    header_set = set(headers)
    missing = [header for header in REQUIRED_POLICE_STREET_HEADERS if header not in header_set]
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(
            f"Police crime schema mismatch; missing required headers: {missing_fields}"
        )


def normalize_police_street_row(
    raw_row: Mapping[str, str],
) -> tuple[PoliceCrimePoint | None, str | None]:
    raw_month = raw_row.get("Month")
    month = _parse_month(raw_month)
    if month is None:
        return None, "invalid_month"

    crime_category = _strip_or_none(raw_row.get("Crime type"))
    if crime_category is None:
        return None, "missing_crime_type"

    longitude_value = raw_row.get("Longitude")
    if _strip_or_none(longitude_value) is None:
        return None, "missing_longitude"
    longitude = _parse_coordinate(longitude_value, axis="longitude")
    if longitude is None:
        return None, "invalid_longitude"

    latitude_value = raw_row.get("Latitude")
    if _strip_or_none(latitude_value) is None:
        return None, "missing_latitude"
    latitude = _parse_coordinate(latitude_value, axis="latitude")
    if latitude is None:
        return None, "invalid_latitude"

    return (
        PoliceCrimePoint(
            month=month,
            crime_category=crime_category,
            longitude=longitude,
            latitude=latitude,
        ),
        None,
    )


class PoliceCrimeContextPipeline:
    source = PipelineSource.POLICE_CRIME_CONTEXT

    def __init__(
        self,
        engine: Engine,
        *,
        source_archive_url: str | None = None,
        source_mode: str = DEFAULT_POLICE_CRIME_SOURCE_MODE,
        crime_radius_meters: float = DEFAULT_POLICE_CRIME_RADIUS_METERS,
    ) -> None:
        self._engine = engine
        self._source_archive_url = source_archive_url
        self._source_mode = _normalize_source_mode(source_mode)
        self._crime_radius_meters = _validate_radius(crime_radius_meters)

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        metadata_path = context.bronze_source_path / BRONZE_METADATA_FILE_NAME
        extracted_dir = context.bronze_source_path / BRONZE_EXTRACTED_DIR
        archive_path = context.bronze_source_path / BRONZE_ARCHIVE_FILE_NAME

        existing_metadata = _load_download_metadata(metadata_path)
        existing_row_count = _parse_int(existing_metadata.get("rows"))
        existing_file_count = _parse_int(existing_metadata.get("extracted_file_count"))
        if (
            existing_row_count is not None
            and existing_file_count is not None
            and extracted_dir.exists()
            and len(list(extracted_dir.glob("*.csv"))) >= existing_file_count
        ):
            return existing_row_count

        if self._source_mode != "archive":
            raise ValueError(
                "CIVITAS_POLICE_CRIME_SOURCE_MODE=api is not supported for bulk context loads. "
                "Use archive mode."
            )

        archive_url = self._source_archive_url or _resolve_latest_archive_url()
        archive_month = _parse_month_from_archive_url(archive_url)

        _copy_from_source(archive_url, archive_path)
        extracted_files = _extract_archive(archive_path, extracted_dir)
        row_count = _count_csv_rows(extracted_files)

        metadata = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "source_mode": self._source_mode,
            "source_archive_url": archive_url,
            "source_month": archive_month,
            "radius_meters": self._crime_radius_meters,
            "sha256": _sha256_file(archive_path),
            "extracted_file_count": len(extracted_files),
            "rows": row_count,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        return row_count

    def stage(self, context: PipelineRunContext) -> StageResult:
        extracted_files = _resolve_extracted_csv_files(context.bronze_source_path)
        if not extracted_files:
            raise ValueError(
                "No extracted Police street-crime CSV files found. Run download stage first."
            )

        staged_rows: list[PoliceCrimePoint] = []
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        for csv_path in extracted_files:
            for headers, raw_row in _iter_csv_rows(csv_path):
                validate_police_street_headers(headers)
                normalized, rejection = normalize_police_street_row(raw_row)
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
                        month date NOT NULL,
                        crime_category text NOT NULL,
                        longitude double precision NOT NULL,
                        latitude double precision NOT NULL,
                        location geography(Point, 4326) NOT NULL
                    )
                    """
                )
            )

            if staged_rows:
                connection.execute(
                    text(
                        f"""
                        INSERT INTO staging.{staging_table_name} (
                            month,
                            crime_category,
                            longitude,
                            latitude,
                            location
                        ) VALUES (
                            :month,
                            :crime_category,
                            :longitude,
                            :latitude,
                            ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography
                        )
                        """
                    ),
                    [
                        {
                            "month": row.month,
                            "crime_category": row.crime_category,
                            "longitude": row.longitude,
                            "latitude": row.latitude,
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
        metadata = _load_download_metadata(context.bronze_source_path / BRONZE_METADATA_FILE_NAME)
        source_month = (
            str(metadata.get("source_month"))
            if isinstance(metadata.get("source_month"), str)
            else None
        )

        with self._engine.begin() as connection:
            if source_month is None:
                source_month = connection.execute(
                    text(
                        f"""
                        SELECT to_char(MAX(month), 'YYYY-MM')
                        FROM staging.{staging_table_name}
                        """
                    )
                ).scalar_one()
            source_month = source_month or "unknown"

            promoted_rows = int(
                connection.execute(
                    text(
                        f"""
                        WITH aggregated AS (
                            SELECT
                                schools.urn AS urn,
                                staged.month AS month,
                                staged.crime_category AS crime_category,
                                COUNT(*)::integer AS incident_count
                            FROM schools
                            INNER JOIN staging.{staging_table_name} AS staged
                                ON ST_DWithin(
                                    schools.location,
                                    staged.location,
                                    :radius_meters
                                )
                            GROUP BY schools.urn, staged.month, staged.crime_category
                        ),
                        upserted AS (
                            INSERT INTO area_crime_context (
                                urn,
                                month,
                                crime_category,
                                incident_count,
                                radius_meters,
                                source_month,
                                updated_at
                            )
                            SELECT
                                aggregated.urn,
                                aggregated.month,
                                aggregated.crime_category,
                                aggregated.incident_count,
                                :radius_meters,
                                :source_month,
                                timezone('utc', now())
                            FROM aggregated
                            ON CONFLICT (urn, month, crime_category, radius_meters) DO UPDATE SET
                                incident_count = EXCLUDED.incident_count,
                                source_month = EXCLUDED.source_month,
                                updated_at = timezone('utc', now())
                            RETURNING 1
                        )
                        SELECT COUNT(*) FROM upserted
                        """
                    ),
                    {
                        "radius_meters": self._crime_radius_meters,
                        "source_month": source_month,
                    },
                ).scalar_one()
            )
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
        return promoted_rows

    @staticmethod
    def _staging_table_name(context: PipelineRunContext) -> str:
        return f"police_crime_context__{context.run_id.hex}"


def _resolve_latest_archive_url() -> str:
    index_html = _download_text(POLICE_ARCHIVE_INDEX_URL)
    return extract_latest_police_archive_url(index_html)


def _normalize_source_mode(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized in SUPPORTED_POLICE_CRIME_SOURCE_MODES:
        return normalized
    msg = "Unsupported police source mode. Expected one of: " + ", ".join(
        sorted(SUPPORTED_POLICE_CRIME_SOURCE_MODES)
    )
    raise ValueError(msg)


def _validate_radius(radius_meters: float) -> float:
    if not math.isfinite(radius_meters) or radius_meters <= 0:
        raise ValueError("CIVITAS_POLICE_CRIME_RADIUS_METERS must be a positive finite number.")
    return radius_meters


def _parse_month(raw_value: str | None) -> date | None:
    value = (raw_value or "").strip()
    if len(value) != 7 or value[4] != "-" or not value[:4].isdigit() or not value[5:].isdigit():
        return None
    year = int(value[:4])
    month = int(value[5:])
    if month < 1 or month > 12:
        return None
    return date(year, month, 1)


def _parse_month_from_archive_url(archive_url: str) -> str | None:
    parsed = urllib.parse.urlparse(archive_url)
    file_name = Path(parsed.path).name
    if len(file_name) >= 11 and file_name[:7].count("-") == 1:
        month = file_name[:7]
        if _parse_month(month) is not None:
            return month
    return None


def _parse_coordinate(raw_value: str | None, *, axis: str) -> float | None:
    value = (raw_value or "").strip()
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    if axis == "longitude" and not (-180.0 <= parsed <= 180.0):
        return None
    if axis == "latitude" and not (-90.0 <= parsed <= 90.0):
        return None
    return parsed


def _strip_or_none(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    return value or None


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
        request = urllib.request.Request(source, headers={"User-Agent": "civitas-pipeline/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response:
            target.write_bytes(response.read())
        return

    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(
            f"Configured Police crime archive source '{source_path}' was not found."
        )
    shutil.copy2(source_path, target)


def _extract_archive(archive_path: Path, output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted_files: list[Path] = []
    with zipfile.ZipFile(archive_path, "r") as archive:
        for member_name in archive.namelist():
            if not member_name.casefold().endswith(".csv"):
                continue
            member_path = Path(member_name)
            if not member_path.name.casefold().endswith("-street.csv"):
                continue
            target_path = output_dir / member_path.name
            with archive.open(member_name) as source_stream:
                target_path.write_bytes(source_stream.read())
            extracted_files.append(target_path)

    if not extracted_files:
        raise ValueError("Police archive did not contain any '*-street.csv' files.")
    return extracted_files


def _resolve_extracted_csv_files(bronze_source_path: Path) -> list[Path]:
    extracted_dir = bronze_source_path / BRONZE_EXTRACTED_DIR
    if extracted_dir.exists():
        files = sorted(path for path in extracted_dir.glob("*.csv") if path.is_file())
        if files:
            return files
    files = sorted(path for path in bronze_source_path.rglob("*-street.csv") if path.is_file())
    return files


def _iter_csv_rows(csv_path: Path) -> list[tuple[list[str], dict[str, str]]]:
    raw_bytes = csv_path.read_bytes()
    last_decode_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            csv_text = raw_bytes.decode(encoding)
        except UnicodeDecodeError as exc:
            last_decode_error = exc
            continue

        reader = csv.DictReader(io.StringIO(csv_text, newline=""))
        if reader.fieldnames is None:
            raise ValueError(f"Police CSV '{csv_path}' has no header row.")
        headers = [field.strip() for field in reader.fieldnames]
        rows = [
            (headers, {key.strip(): value for key, value in row.items() if key is not None})
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]
        return rows

    if last_decode_error is not None:
        raise last_decode_error
    raise ValueError(f"Unable to decode Police CSV at '{csv_path}'.")


def _count_csv_rows(csv_paths: Sequence[Path]) -> int:
    total_rows = 0
    for csv_path in csv_paths:
        for _headers, _row in _iter_csv_rows(csv_path):
            total_rows += 1
    return total_rows


def _parse_int(raw_value: object) -> int | None:
    if isinstance(raw_value, int):
        return raw_value
    if isinstance(raw_value, str):
        with suppress(ValueError):
            return int(raw_value)
    return None


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
