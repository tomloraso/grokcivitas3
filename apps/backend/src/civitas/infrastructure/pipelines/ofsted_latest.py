from __future__ import annotations

import csv
import gzip
import hashlib
import html
import io
import json
import re
import shutil
import urllib.parse
import urllib.request
from contextlib import suppress
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import ofsted_latest as ofsted_latest_contract

OFSTED_LANDING_PAGE_URL = (
    "https://www.gov.uk/government/statistical-data-sets/"
    "monthly-management-information-ofsteds-school-inspections-outcomes"
)
REQUIRED_OFSTED_LATEST_HEADERS = ofsted_latest_contract.REQUIRED_HEADERS
JUDGEMENT_CODE_TO_LABEL = ofsted_latest_contract.JUDGEMENT_CODE_TO_LABEL
BRONZE_FILE_NAME = "latest_inspections.csv"
_HREF_PATTERN = re.compile(r"""href=["']([^"']+)["']""", re.IGNORECASE)
_ASSET_URL_PREFIX = "https://assets.publishing.service.gov.uk/"
_MONTH_PATTERN = re.compile(
    r"_(?:as_at|at)_(?P<day>\d{1,2})_(?P<month>[A-Za-z]+)_(?P<year>\d{4})\.csv",
    re.IGNORECASE,
)
_MONTH_ABBR_TO_NUMBER: dict[str, int] = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
OFSTED_LATEST_NORMALIZATION_CONTRACT_VERSION = ofsted_latest_contract.CONTRACT_VERSION


@dataclass(frozen=True)
class OfstedLatestStagedRow:
    urn: str
    provider_page_url: str
    inspection_start_date: date | None
    publication_date: date | None
    overall_effectiveness_code: str | None
    overall_effectiveness_label: str | None
    latest_oeif_inspection_start_date: date | None
    latest_oeif_publication_date: date | None
    quality_of_education_code: str | None
    quality_of_education_label: str | None
    behaviour_and_attitudes_code: str | None
    behaviour_and_attitudes_label: str | None
    personal_development_code: str | None
    personal_development_label: str | None
    leadership_and_management_code: str | None
    leadership_and_management_label: str | None
    latest_ungraded_inspection_date: date | None
    latest_ungraded_publication_date: date | None
    is_graded: bool
    ungraded_outcome: str | None
    source_asset_url: str
    source_asset_month: str | None


def validate_ofsted_latest_headers(headers: Sequence[str]) -> None:
    ofsted_latest_contract.validate_headers(headers)


def extract_latest_ofsted_asset_url(landing_page_html: str) -> str:
    matched_urls: list[str] = []
    seen_urls: set[str] = set()
    for match in _HREF_PATTERN.finditer(landing_page_html):
        href = html.unescape(match.group(1)).strip()
        normalized_href = _normalize_asset_href(href)
        if normalized_href is None:
            continue
        if _is_latest_ofsted_asset_url(normalized_href) and normalized_href not in seen_urls:
            seen_urls.add(normalized_href)
            matched_urls.append(normalized_href)

    if not matched_urls:
        raise ValueError("Unable to resolve latest Ofsted asset URL from landing page.")

    ranked_urls = sorted(
        matched_urls,
        key=lambda url: (_asset_sort_date(url), url),
        reverse=True,
    )
    return ranked_urls[0]


def normalize_ofsted_latest_row(
    raw_row: Mapping[str, str],
    *,
    source_asset_url: str,
    source_asset_month: str | None,
) -> tuple[OfstedLatestStagedRow | None, str | None]:
    normalized_row, rejection = ofsted_latest_contract.normalize_row(
        raw_row,
        source_asset_url=source_asset_url,
        source_asset_month=source_asset_month,
    )
    if normalized_row is None:
        return None, rejection
    return (
        OfstedLatestStagedRow(
            urn=normalized_row["urn"],
            provider_page_url=normalized_row["provider_page_url"],
            inspection_start_date=normalized_row["inspection_start_date"],
            publication_date=normalized_row["publication_date"],
            overall_effectiveness_code=normalized_row["overall_effectiveness_code"],
            overall_effectiveness_label=normalized_row["overall_effectiveness_label"],
            latest_oeif_inspection_start_date=normalized_row["latest_oeif_inspection_start_date"],
            latest_oeif_publication_date=normalized_row["latest_oeif_publication_date"],
            quality_of_education_code=normalized_row["quality_of_education_code"],
            quality_of_education_label=normalized_row["quality_of_education_label"],
            behaviour_and_attitudes_code=normalized_row["behaviour_and_attitudes_code"],
            behaviour_and_attitudes_label=normalized_row["behaviour_and_attitudes_label"],
            personal_development_code=normalized_row["personal_development_code"],
            personal_development_label=normalized_row["personal_development_label"],
            leadership_and_management_code=normalized_row["leadership_and_management_code"],
            leadership_and_management_label=normalized_row["leadership_and_management_label"],
            latest_ungraded_inspection_date=normalized_row["latest_ungraded_inspection_date"],
            latest_ungraded_publication_date=normalized_row["latest_ungraded_publication_date"],
            is_graded=normalized_row["is_graded"],
            ungraded_outcome=normalized_row["ungraded_outcome"],
            source_asset_url=normalized_row["source_asset_url"],
            source_asset_month=normalized_row["source_asset_month"],
        ),
        None,
    )


class OfstedLatestPipeline:
    source = PipelineSource.OFSTED_LATEST

    def __init__(self, engine: Engine, source_csv: str | None = None) -> None:
        self._engine = engine
        self._source_csv = source_csv

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)

        target_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if target_csv.exists():
            return _count_csv_rows(target_csv)

        source_asset_url = self._source_csv
        source_asset_month = _infer_source_asset_month(source_asset_url)
        if source_asset_url is None:
            landing_page_html = _download_text(OFSTED_LANDING_PAGE_URL)
            source_asset_url = extract_latest_ofsted_asset_url(landing_page_html)
            source_asset_month = _infer_source_asset_month(source_asset_url)
            target_csv.write_text(_download_text(source_asset_url), encoding="utf-8")
        else:
            _copy_from_source(source_asset_url, target_csv)

        return self._finalize_download_metadata(
            target_csv=target_csv,
            source_asset_url=source_asset_url,
            source_asset_month=source_asset_month,
        )

    def stage(self, context: PipelineRunContext) -> StageResult:
        source_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if not source_csv.exists():
            raise FileNotFoundError(
                f"Ofsted latest bronze file not found at '{source_csv}'. Run download stage first."
            )

        metadata = _load_download_metadata(source_csv.with_suffix(".metadata.json"))
        source_asset_url = str(metadata.get("source_asset_url") or "")
        if not source_asset_url:
            raise ValueError("Ofsted latest metadata missing 'source_asset_url'.")
        source_asset_month_value = metadata.get("source_asset_month")
        source_asset_month = (
            str(source_asset_month_value) if isinstance(source_asset_month_value, str) else None
        )

        headers, rows = _read_csv_rows(source_csv)
        validate_ofsted_latest_headers(headers)

        staged_rows_by_urn: dict[str, OfstedLatestStagedRow] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        for raw_row in rows:
            normalized, rejection = normalize_ofsted_latest_row(
                raw_row,
                source_asset_url=source_asset_url,
                source_asset_month=source_asset_month,
            )
            if normalized is not None:
                existing = staged_rows_by_urn.get(normalized.urn)
                if existing is None or _is_more_recent_ofsted_row(normalized, existing):
                    staged_rows_by_urn[normalized.urn] = normalized
                continue
            if rejection is not None:
                rejected_rows.append((rejection, dict(raw_row)))

        staged_rows = list(staged_rows_by_urn.values())
        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
            connection.execute(
                text(
                    f"""
                    CREATE TABLE staging.{staging_table_name} (
                        urn text PRIMARY KEY,
                        provider_page_url text NOT NULL,
                        inspection_start_date date NULL,
                        publication_date date NULL,
                        overall_effectiveness_code text NULL,
                        overall_effectiveness_label text NULL,
                        latest_oeif_inspection_start_date date NULL,
                        latest_oeif_publication_date date NULL,
                        quality_of_education_code text NULL,
                        quality_of_education_label text NULL,
                        behaviour_and_attitudes_code text NULL,
                        behaviour_and_attitudes_label text NULL,
                        personal_development_code text NULL,
                        personal_development_label text NULL,
                        leadership_and_management_code text NULL,
                        leadership_and_management_label text NULL,
                        latest_ungraded_inspection_date date NULL,
                        latest_ungraded_publication_date date NULL,
                        is_graded boolean NOT NULL,
                        ungraded_outcome text NULL,
                        source_asset_url text NOT NULL,
                        source_asset_month text NULL
                    )
                    """
                )
            )

            if staged_rows:
                staged_insert = text(
                    f"""
                    INSERT INTO staging.{staging_table_name} (
                        urn,
                        provider_page_url,
                        inspection_start_date,
                        publication_date,
                        overall_effectiveness_code,
                        overall_effectiveness_label,
                        latest_oeif_inspection_start_date,
                        latest_oeif_publication_date,
                        quality_of_education_code,
                        quality_of_education_label,
                        behaviour_and_attitudes_code,
                        behaviour_and_attitudes_label,
                        personal_development_code,
                        personal_development_label,
                        leadership_and_management_code,
                        leadership_and_management_label,
                        latest_ungraded_inspection_date,
                        latest_ungraded_publication_date,
                        is_graded,
                        ungraded_outcome,
                        source_asset_url,
                        source_asset_month
                    ) VALUES (
                        :urn,
                        :provider_page_url,
                        :inspection_start_date,
                        :publication_date,
                        :overall_effectiveness_code,
                        :overall_effectiveness_label,
                        :latest_oeif_inspection_start_date,
                        :latest_oeif_publication_date,
                        :quality_of_education_code,
                        :quality_of_education_label,
                        :behaviour_and_attitudes_code,
                        :behaviour_and_attitudes_label,
                        :personal_development_code,
                        :personal_development_label,
                        :leadership_and_management_code,
                        :leadership_and_management_label,
                        :latest_ungraded_inspection_date,
                        :latest_ungraded_publication_date,
                        :is_graded,
                        :ungraded_outcome,
                        :source_asset_url,
                        :source_asset_month
                    )
                    ON CONFLICT (urn) DO UPDATE SET
                        provider_page_url = EXCLUDED.provider_page_url,
                        inspection_start_date = EXCLUDED.inspection_start_date,
                        publication_date = EXCLUDED.publication_date,
                        overall_effectiveness_code = EXCLUDED.overall_effectiveness_code,
                        overall_effectiveness_label = EXCLUDED.overall_effectiveness_label,
                        latest_oeif_inspection_start_date = EXCLUDED.latest_oeif_inspection_start_date,
                        latest_oeif_publication_date = EXCLUDED.latest_oeif_publication_date,
                        quality_of_education_code = EXCLUDED.quality_of_education_code,
                        quality_of_education_label = EXCLUDED.quality_of_education_label,
                        behaviour_and_attitudes_code = EXCLUDED.behaviour_and_attitudes_code,
                        behaviour_and_attitudes_label = EXCLUDED.behaviour_and_attitudes_label,
                        personal_development_code = EXCLUDED.personal_development_code,
                        personal_development_label = EXCLUDED.personal_development_label,
                        leadership_and_management_code = EXCLUDED.leadership_and_management_code,
                        leadership_and_management_label = EXCLUDED.leadership_and_management_label,
                        latest_ungraded_inspection_date = EXCLUDED.latest_ungraded_inspection_date,
                        latest_ungraded_publication_date = EXCLUDED.latest_ungraded_publication_date,
                        is_graded = EXCLUDED.is_graded,
                        ungraded_outcome = EXCLUDED.ungraded_outcome,
                        source_asset_url = EXCLUDED.source_asset_url,
                        source_asset_month = EXCLUDED.source_asset_month
                    """
                )
                for rows_chunk in chunked(staged_rows, context.stage_chunk_size):
                    connection.execute(
                        staged_insert,
                        [
                            {
                                "urn": row.urn,
                                "provider_page_url": row.provider_page_url,
                                "inspection_start_date": row.inspection_start_date,
                                "publication_date": row.publication_date,
                                "overall_effectiveness_code": row.overall_effectiveness_code,
                                "overall_effectiveness_label": row.overall_effectiveness_label,
                                "latest_oeif_inspection_start_date": row.latest_oeif_inspection_start_date,
                                "latest_oeif_publication_date": row.latest_oeif_publication_date,
                                "quality_of_education_code": row.quality_of_education_code,
                                "quality_of_education_label": row.quality_of_education_label,
                                "behaviour_and_attitudes_code": row.behaviour_and_attitudes_code,
                                "behaviour_and_attitudes_label": row.behaviour_and_attitudes_label,
                                "personal_development_code": row.personal_development_code,
                                "personal_development_label": row.personal_development_label,
                                "leadership_and_management_code": row.leadership_and_management_code,
                                "leadership_and_management_label": row.leadership_and_management_label,
                                "latest_ungraded_inspection_date": row.latest_ungraded_inspection_date,
                                "latest_ungraded_publication_date": row.latest_ungraded_publication_date,
                                "is_graded": row.is_graded,
                                "ungraded_outcome": row.ungraded_outcome,
                                "source_asset_url": row.source_asset_url,
                                "source_asset_month": row.source_asset_month,
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
            contract_version=OFSTED_LATEST_NORMALIZATION_CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            promoted_rows = int(
                connection.execute(
                    text(
                        f"""
                        WITH upserted AS (
                            INSERT INTO school_ofsted_latest (
                                urn,
                                provider_page_url,
                                inspection_start_date,
                                publication_date,
                                overall_effectiveness_code,
                                overall_effectiveness_label,
                                latest_oeif_inspection_start_date,
                                latest_oeif_publication_date,
                                quality_of_education_code,
                                quality_of_education_label,
                                behaviour_and_attitudes_code,
                                behaviour_and_attitudes_label,
                                personal_development_code,
                                personal_development_label,
                                leadership_and_management_code,
                                leadership_and_management_label,
                                latest_ungraded_inspection_date,
                                latest_ungraded_publication_date,
                                is_graded,
                                ungraded_outcome,
                                source_asset_url,
                                source_asset_month,
                                updated_at
                            )
                            SELECT
                                staged.urn,
                                staged.provider_page_url,
                                staged.inspection_start_date,
                                staged.publication_date,
                                staged.overall_effectiveness_code,
                                staged.overall_effectiveness_label,
                                staged.latest_oeif_inspection_start_date,
                                staged.latest_oeif_publication_date,
                                staged.quality_of_education_code,
                                staged.quality_of_education_label,
                                staged.behaviour_and_attitudes_code,
                                staged.behaviour_and_attitudes_label,
                                staged.personal_development_code,
                                staged.personal_development_label,
                                staged.leadership_and_management_code,
                                staged.leadership_and_management_label,
                                staged.latest_ungraded_inspection_date,
                                staged.latest_ungraded_publication_date,
                                staged.is_graded,
                                staged.ungraded_outcome,
                                staged.source_asset_url,
                                staged.source_asset_month,
                                timezone('utc', now())
                            FROM staging.{staging_table_name} AS staged
                            INNER JOIN schools ON schools.urn = staged.urn
                            ON CONFLICT (urn) DO UPDATE SET
                                provider_page_url = EXCLUDED.provider_page_url,
                                inspection_start_date = EXCLUDED.inspection_start_date,
                                publication_date = EXCLUDED.publication_date,
                                overall_effectiveness_code = EXCLUDED.overall_effectiveness_code,
                                overall_effectiveness_label = EXCLUDED.overall_effectiveness_label,
                                latest_oeif_inspection_start_date = EXCLUDED.latest_oeif_inspection_start_date,
                                latest_oeif_publication_date = EXCLUDED.latest_oeif_publication_date,
                                quality_of_education_code = EXCLUDED.quality_of_education_code,
                                quality_of_education_label = EXCLUDED.quality_of_education_label,
                                behaviour_and_attitudes_code = EXCLUDED.behaviour_and_attitudes_code,
                                behaviour_and_attitudes_label = EXCLUDED.behaviour_and_attitudes_label,
                                personal_development_code = EXCLUDED.personal_development_code,
                                personal_development_label = EXCLUDED.personal_development_label,
                                leadership_and_management_code = EXCLUDED.leadership_and_management_code,
                                leadership_and_management_label = EXCLUDED.leadership_and_management_label,
                                latest_ungraded_inspection_date = EXCLUDED.latest_ungraded_inspection_date,
                                latest_ungraded_publication_date = EXCLUDED.latest_ungraded_publication_date,
                                is_graded = EXCLUDED.is_graded,
                                ungraded_outcome = EXCLUDED.ungraded_outcome,
                                source_asset_url = EXCLUDED.source_asset_url,
                                source_asset_month = EXCLUDED.source_asset_month,
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
        return f"ofsted_latest__{context.run_id.hex}"

    def _finalize_download_metadata(
        self,
        *,
        target_csv: Path,
        source_asset_url: str,
        source_asset_month: str | None,
    ) -> int:
        row_count = _count_csv_rows(target_csv)
        metadata_path = target_csv.with_suffix(".metadata.json")
        metadata = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "landing_page_url": OFSTED_LANDING_PAGE_URL,
            "source_asset_url": source_asset_url,
            "source_asset_month": source_asset_month,
            "normalization_contract_version": OFSTED_LATEST_NORMALIZATION_CONTRACT_VERSION,
            "sha256": _sha256_file(target_csv),
            "rows": row_count,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        return row_count


def _read_csv_rows(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    raw_bytes = csv_path.read_bytes()
    last_decode_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            csv_text = raw_bytes.decode(encoding)
        except UnicodeDecodeError as exc:
            last_decode_error = exc
            continue

        reader = csv.DictReader(io.StringIO(csv_text))
        if reader.fieldnames is None:
            raise ValueError("Ofsted latest CSV has no header row.")
        return list(reader.fieldnames), list(reader)

    if last_decode_error is not None:
        raise last_decode_error
    raise ValueError(f"Unable to decode Ofsted latest CSV at '{csv_path}'.")


def _count_csv_rows(csv_path: Path) -> int:
    _, rows = _read_csv_rows(csv_path)
    return len(rows)


def _normalize_asset_href(raw_href: str) -> str | None:
    if not raw_href:
        return None
    if raw_href.startswith("//assets.publishing.service.gov.uk/"):
        return f"https:{raw_href}"
    if raw_href.startswith(_ASSET_URL_PREFIX):
        return raw_href
    return None


def _is_latest_ofsted_asset_url(url: str) -> bool:
    lowered = url.casefold()
    return (
        lowered.startswith(_ASSET_URL_PREFIX)
        and "latest_inspections" in lowered
        and lowered.endswith(".csv")
    )


def _infer_source_asset_month(source_asset_url: str | None) -> str | None:
    if source_asset_url is None:
        return None

    match = _MONTH_PATTERN.search(source_asset_url)
    if match is None:
        return None

    month_token = match.group("month").strip().casefold()[:3]
    month_number = _MONTH_ABBR_TO_NUMBER.get(month_token)
    if month_number is None:
        return None

    year = int(match.group("year"))
    return f"{year:04d}-{month_number:02d}"


def _asset_sort_date(source_asset_url: str) -> tuple[int, int, int]:
    match = _MONTH_PATTERN.search(source_asset_url)
    if match is None:
        return (0, 0, 0)

    month_token = match.group("month").strip().casefold()[:3]
    month_number = _MONTH_ABBR_TO_NUMBER.get(month_token)
    if month_number is None:
        return (0, 0, 0)

    year = int(match.group("year"))
    day = int(match.group("day"))
    return (year, month_number, day)


def _is_more_recent_ofsted_row(
    candidate: OfstedLatestStagedRow,
    existing: OfstedLatestStagedRow,
) -> bool:
    candidate_key = (
        candidate.inspection_start_date or date.min,
        candidate.publication_date or date.min,
        candidate.is_graded,
        candidate.overall_effectiveness_code or "",
        candidate.ungraded_outcome or "",
    )
    existing_key = (
        existing.inspection_start_date or date.min,
        existing.publication_date or date.min,
        existing.is_graded,
        existing.overall_effectiveness_code or "",
        existing.ungraded_outcome or "",
    )
    return candidate_key > existing_key


def _normalize_overall_effectiveness_code(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        raise ValueError("empty overall effectiveness code")

    if value.casefold() == "not judged":
        return "Not judged"

    with suppress(ValueError):
        numeric_value = float(value)
        if numeric_value in {1.0, 2.0, 3.0, 4.0} and numeric_value.is_integer():
            return str(int(numeric_value))

    if value in {"1", "2", "3", "4"}:
        return value

    return value


def _parse_optional_date(raw_value: str | None) -> date | None:
    value = (raw_value or "").strip()
    if not value or value.upper() == "NULL":
        return None

    supported_formats = (
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
    )
    for date_format in supported_formats:
        with suppress(ValueError):
            return datetime.strptime(value, date_format).date()
    raise ValueError(f"unsupported date value '{value}'")


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
        return _decode_response_bytes(response.read(), response.headers.get("Content-Encoding"))


def _copy_from_source(source: str, target: Path) -> None:
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        target.write_text(_download_text(source), encoding="utf-8")
        return

    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"Configured Ofsted source CSV path '{source_path}' was not found.")
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
