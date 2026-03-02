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

from .base import PipelineRunContext, PipelineSource, StageResult

OFSTED_LANDING_PAGE_URL = (
    "https://www.gov.uk/government/statistical-data-sets/"
    "monthly-management-information-ofsteds-school-inspections-outcomes"
)
BRONZE_MANIFEST_FILE_NAME = "assets.manifest.json"

SCHEMA_VERSION_YTD = "all_inspections_ytd"
SCHEMA_VERSION_HISTORICAL_2015_2019 = "all_inspections_historical_2015_2019"

REQUIRED_OFSTED_TIMELINE_YTD_HEADERS: tuple[str, ...] = (
    "URN",
    "Inspection number",
    "Inspection type",
    "Inspection start date",
    "Publication date",
)
REQUIRED_OFSTED_TIMELINE_HISTORICAL_HEADERS: tuple[str, ...] = (
    "Academic year",
    "URN",
    "Inspection number",
    "Inspection start date",
    "Publication date",
    "Overall effectiveness",
)
OVERALL_EFFECTIVENESS_CODE_TO_LABEL: dict[str, str] = {
    "1": "Outstanding",
    "2": "Good",
    "3": "Requires improvement",
    "4": "Inadequate",
    "Not judged": "Not judged",
}
OVERALL_EFFECTIVENESS_LABEL_TO_CODE: dict[str, str] = {
    label.casefold(): code for code, label in OVERALL_EFFECTIVENESS_CODE_TO_LABEL.items()
}

_HREF_PATTERN = re.compile(r"""href=["']([^"']+)["']""", re.IGNORECASE)
_ASSET_URL_PREFIX = "https://assets.publishing.service.gov.uk/"
_ASSET_DATE_PATTERN = re.compile(
    r"_(?P<day>\d{1,2})_(?P<month>[A-Za-z]{3})_(?P<year>\d{4})\.csv$",
    re.IGNORECASE,
)
_HISTORICAL_ASSET_TOKEN = "1_september_2015_to_31_august_2019"
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


@dataclass(frozen=True)
class OfstedTimelineStagedRow:
    inspection_number: str
    urn: str
    inspection_start_date: date
    inspection_end_date: date | None
    publication_date: date | None
    inspection_type: str | None
    inspection_type_grouping: str | None
    event_type_grouping: str | None
    overall_effectiveness_code: str | None
    overall_effectiveness_label: str | None
    headline_outcome_text: str | None
    category_of_concern: str | None
    source_schema_version: str
    source_asset_url: str
    source_asset_month: str | None


@dataclass(frozen=True)
class OfstedTimelineAsset:
    source_asset_url: str
    source_schema_hint: str
    source_asset_month: str | None


def validate_ofsted_timeline_headers(headers: Sequence[str], *, schema_version: str) -> None:
    required_headers = (
        REQUIRED_OFSTED_TIMELINE_HISTORICAL_HEADERS
        if schema_version == SCHEMA_VERSION_HISTORICAL_2015_2019
        else REQUIRED_OFSTED_TIMELINE_YTD_HEADERS
    )
    header_set = set(headers)
    missing = [header for header in required_headers if header not in header_set]
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(
            f"Ofsted timeline schema mismatch for '{schema_version}'; missing required headers: "
            f"{missing_fields}"
        )


def extract_ofsted_timeline_asset_urls(
    landing_page_html: str,
) -> tuple[str, str, str | None]:
    matched_urls: list[str] = []
    seen_urls: set[str] = set()
    for match in _HREF_PATTERN.finditer(landing_page_html):
        href = html.unescape(match.group(1)).strip()
        normalized_href = _normalize_asset_href(href)
        if normalized_href is None:
            continue
        if not normalized_href.casefold().endswith(".csv"):
            continue
        if normalized_href in seen_urls:
            continue
        seen_urls.add(normalized_href)
        matched_urls.append(normalized_href)

    if not matched_urls:
        raise ValueError("Unable to resolve Ofsted timeline asset URLs from landing page.")

    all_inspections_candidates = [
        url for url in matched_urls if "all_inspections" in url.casefold()
    ]
    latest_inspections_candidates = [
        url for url in matched_urls if "latest_inspections" in url.casefold()
    ]
    historical_candidates = [
        url for url in matched_urls if _HISTORICAL_ASSET_TOKEN in url.casefold()
    ]

    all_inspections_url = _select_latest_dated_asset_url(all_inspections_candidates)
    latest_inspections_url = _select_latest_dated_asset_url(latest_inspections_candidates)
    historical_url = historical_candidates[0] if historical_candidates else None

    if all_inspections_url is None:
        raise ValueError("Unable to resolve Ofsted all_inspections timeline CSV asset URL.")
    if latest_inspections_url is None:
        raise ValueError("Unable to resolve Ofsted latest_inspections CSV asset URL.")

    return all_inspections_url, latest_inspections_url, historical_url


def normalize_ofsted_timeline_row(
    raw_row: Mapping[str, str],
    *,
    source_schema_version: str,
    source_asset_url: str,
    source_asset_month: str | None,
) -> tuple[OfstedTimelineStagedRow | None, str | None]:
    urn = _strip_or_none(raw_row.get("URN"))
    if urn is None:
        return None, "missing_urn"

    inspection_number = _strip_or_none(raw_row.get("Inspection number"))
    if inspection_number is None:
        return None, "missing_inspection_number"

    inspection_start_raw = raw_row.get("Inspection start date")
    try:
        inspection_start_date = _parse_required_date(inspection_start_raw)
    except ValueError:
        return None, "invalid_inspection_start_date"

    try:
        inspection_end_date = _parse_optional_date(raw_row.get("Inspection end date"))
    except ValueError:
        return None, "invalid_inspection_end_date"

    try:
        publication_date = _parse_optional_date(raw_row.get("Publication date"))
    except ValueError:
        return None, "invalid_publication_date"

    overall_effectiveness_raw = _first_non_empty(
        raw_row,
        [
            "Latest OEIF overall effectiveness",
            "Overall effectiveness",
        ],
    )
    overall_effectiveness_code: str | None = None
    overall_effectiveness_label: str | None = None
    if overall_effectiveness_raw is not None:
        overall_effectiveness_code = _normalize_overall_effectiveness_code(
            overall_effectiveness_raw
        )
        if overall_effectiveness_code is not None:
            overall_effectiveness_label = OVERALL_EFFECTIVENESS_CODE_TO_LABEL[
                overall_effectiveness_code
            ]

    headline_outcome_text = _first_non_empty(
        raw_row,
        [
            "Ungraded inspection overall outcome",
            "Outcome",
        ],
    )
    if headline_outcome_text is None and overall_effectiveness_code is None:
        headline_outcome_text = overall_effectiveness_raw

    return (
        OfstedTimelineStagedRow(
            inspection_number=inspection_number,
            urn=urn,
            inspection_start_date=inspection_start_date,
            inspection_end_date=inspection_end_date,
            publication_date=publication_date,
            inspection_type=_first_non_empty(raw_row, ["Inspection type"]),
            inspection_type_grouping=_first_non_empty(raw_row, ["Inspection type grouping"]),
            event_type_grouping=_first_non_empty(raw_row, ["Event type grouping"]),
            overall_effectiveness_code=overall_effectiveness_code,
            overall_effectiveness_label=overall_effectiveness_label,
            headline_outcome_text=headline_outcome_text,
            category_of_concern=_first_non_empty(raw_row, ["Category of concern"]),
            source_schema_version=source_schema_version,
            source_asset_url=source_asset_url,
            source_asset_month=source_asset_month,
        ),
        None,
    )


class OfstedTimelinePipeline:
    source = PipelineSource.OFSTED_TIMELINE

    def __init__(
        self,
        engine: Engine,
        *,
        source_index_url: str = OFSTED_LANDING_PAGE_URL,
        source_assets_csv: str | None = None,
        include_historical_baseline: bool = True,
    ) -> None:
        self._engine = engine
        self._source_index_url = source_index_url
        self._source_assets_csv = source_assets_csv
        self._include_historical_baseline = include_historical_baseline

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME

        existing_manifest = _load_manifest(manifest_path)
        existing_assets = _manifest_assets(existing_manifest)
        existing_file_names = [_manifest_asset_file_name(asset) for asset in existing_assets]
        if existing_assets and all(
            file_name is not None and (context.bronze_source_path / file_name).exists()
            for file_name in existing_file_names
        ):
            return sum(_manifest_asset_row_count(asset) for asset in existing_assets)

        resolved_assets = self._resolve_assets()
        manifest_assets: list[dict[str, object]] = []
        total_rows = 0

        for index, asset in enumerate(resolved_assets, start=1):
            target_file_name = _build_bronze_asset_file_name(asset.source_asset_url, index=index)
            target_path = context.bronze_source_path / target_file_name
            _copy_from_source(asset.source_asset_url, target_path)

            row_count = _count_csv_rows(target_path, schema_hint=asset.source_schema_hint)
            total_rows += row_count
            manifest_assets.append(
                {
                    "source_asset_url": asset.source_asset_url,
                    "source_schema_hint": asset.source_schema_hint,
                    "source_asset_month": asset.source_asset_month,
                    "bronze_file_name": target_file_name,
                    "sha256": _sha256_file(target_path),
                    "rows": row_count,
                }
            )

        manifest_payload = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "source_index_url": self._source_index_url,
            "assets": manifest_assets,
        }
        manifest_path.write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True), encoding="utf-8"
        )
        return total_rows

    def stage(self, context: PipelineRunContext) -> StageResult:
        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
        manifest = _load_manifest(manifest_path)
        manifest_assets = _manifest_assets(manifest)
        if not manifest_assets:
            raise ValueError(
                "Ofsted timeline manifest missing assets. Run download stage before stage."
            )

        staged_rows_by_inspection: dict[str, OfstedTimelineStagedRow] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []

        for manifest_asset in manifest_assets:
            bronze_file_name = str(manifest_asset["bronze_file_name"])
            source_asset_url = str(manifest_asset.get("source_asset_url") or bronze_file_name)
            source_asset_month = _normalize_month(
                str(manifest_asset["source_asset_month"])
                if isinstance(manifest_asset.get("source_asset_month"), str)
                else None
            )
            schema_hint = (
                str(manifest_asset["source_schema_hint"])
                if isinstance(manifest_asset.get("source_schema_hint"), str)
                else SCHEMA_VERSION_YTD
            )

            asset_path = context.bronze_source_path / bronze_file_name
            if not asset_path.exists():
                raise FileNotFoundError(
                    f"Ofsted timeline bronze asset '{bronze_file_name}' not found."
                )

            headers, raw_rows, source_schema_version = _read_csv_rows(
                asset_path,
                schema_hint=schema_hint,
            )
            validate_ofsted_timeline_headers(headers, schema_version=source_schema_version)

            for raw_row in raw_rows:
                normalized, rejection = normalize_ofsted_timeline_row(
                    raw_row,
                    source_schema_version=source_schema_version,
                    source_asset_url=source_asset_url,
                    source_asset_month=source_asset_month,
                )
                if normalized is not None:
                    existing = staged_rows_by_inspection.get(normalized.inspection_number)
                    if existing is None or _is_more_recent_timeline_row(normalized, existing):
                        staged_rows_by_inspection[normalized.inspection_number] = normalized
                    continue
                if rejection is not None:
                    rejected_rows.append((rejection, dict(raw_row)))

        staged_rows = list(staged_rows_by_inspection.values())
        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
            connection.execute(
                text(
                    f"""
                    CREATE TABLE staging.{staging_table_name} (
                        inspection_number text PRIMARY KEY,
                        urn text NOT NULL,
                        inspection_start_date date NOT NULL,
                        inspection_end_date date NULL,
                        publication_date date NULL,
                        inspection_type text NULL,
                        inspection_type_grouping text NULL,
                        event_type_grouping text NULL,
                        overall_effectiveness_code text NULL,
                        overall_effectiveness_label text NULL,
                        headline_outcome_text text NULL,
                        category_of_concern text NULL,
                        source_schema_version text NOT NULL,
                        source_asset_url text NOT NULL,
                        source_asset_month text NULL
                    )
                    """
                )
            )

            if staged_rows:
                connection.execute(
                    text(
                        f"""
                        INSERT INTO staging.{staging_table_name} (
                            inspection_number,
                            urn,
                            inspection_start_date,
                            inspection_end_date,
                            publication_date,
                            inspection_type,
                            inspection_type_grouping,
                            event_type_grouping,
                            overall_effectiveness_code,
                            overall_effectiveness_label,
                            headline_outcome_text,
                            category_of_concern,
                            source_schema_version,
                            source_asset_url,
                            source_asset_month
                        ) VALUES (
                            :inspection_number,
                            :urn,
                            :inspection_start_date,
                            :inspection_end_date,
                            :publication_date,
                            :inspection_type,
                            :inspection_type_grouping,
                            :event_type_grouping,
                            :overall_effectiveness_code,
                            :overall_effectiveness_label,
                            :headline_outcome_text,
                            :category_of_concern,
                            :source_schema_version,
                            :source_asset_url,
                            :source_asset_month
                        )
                        ON CONFLICT (inspection_number) DO UPDATE SET
                            urn = EXCLUDED.urn,
                            inspection_start_date = EXCLUDED.inspection_start_date,
                            inspection_end_date = EXCLUDED.inspection_end_date,
                            publication_date = EXCLUDED.publication_date,
                            inspection_type = EXCLUDED.inspection_type,
                            inspection_type_grouping = EXCLUDED.inspection_type_grouping,
                            event_type_grouping = EXCLUDED.event_type_grouping,
                            overall_effectiveness_code = EXCLUDED.overall_effectiveness_code,
                            overall_effectiveness_label = EXCLUDED.overall_effectiveness_label,
                            headline_outcome_text = EXCLUDED.headline_outcome_text,
                            category_of_concern = EXCLUDED.category_of_concern,
                            source_schema_version = EXCLUDED.source_schema_version,
                            source_asset_url = EXCLUDED.source_asset_url,
                            source_asset_month = EXCLUDED.source_asset_month
                        """
                    ),
                    [
                        {
                            "inspection_number": row.inspection_number,
                            "urn": row.urn,
                            "inspection_start_date": row.inspection_start_date,
                            "inspection_end_date": row.inspection_end_date,
                            "publication_date": row.publication_date,
                            "inspection_type": row.inspection_type,
                            "inspection_type_grouping": row.inspection_type_grouping,
                            "event_type_grouping": row.event_type_grouping,
                            "overall_effectiveness_code": row.overall_effectiveness_code,
                            "overall_effectiveness_label": row.overall_effectiveness_label,
                            "headline_outcome_text": row.headline_outcome_text,
                            "category_of_concern": row.category_of_concern,
                            "source_schema_version": row.source_schema_version,
                            "source_asset_url": row.source_asset_url,
                            "source_asset_month": row.source_asset_month,
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
                            INSERT INTO ofsted_inspections (
                                inspection_number,
                                urn,
                                inspection_start_date,
                                inspection_end_date,
                                publication_date,
                                inspection_type,
                                inspection_type_grouping,
                                event_type_grouping,
                                overall_effectiveness_code,
                                overall_effectiveness_label,
                                headline_outcome_text,
                                category_of_concern,
                                source_schema_version,
                                source_asset_url,
                                source_asset_month,
                                updated_at
                            )
                            SELECT
                                staged.inspection_number,
                                staged.urn,
                                staged.inspection_start_date,
                                staged.inspection_end_date,
                                staged.publication_date,
                                staged.inspection_type,
                                staged.inspection_type_grouping,
                                staged.event_type_grouping,
                                staged.overall_effectiveness_code,
                                staged.overall_effectiveness_label,
                                staged.headline_outcome_text,
                                staged.category_of_concern,
                                staged.source_schema_version,
                                staged.source_asset_url,
                                staged.source_asset_month,
                                timezone('utc', now())
                            FROM staging.{staging_table_name} AS staged
                            INNER JOIN schools ON schools.urn = staged.urn
                            ON CONFLICT (inspection_number) DO UPDATE SET
                                urn = EXCLUDED.urn,
                                inspection_start_date = EXCLUDED.inspection_start_date,
                                inspection_end_date = EXCLUDED.inspection_end_date,
                                publication_date = EXCLUDED.publication_date,
                                inspection_type = EXCLUDED.inspection_type,
                                inspection_type_grouping = EXCLUDED.inspection_type_grouping,
                                event_type_grouping = EXCLUDED.event_type_grouping,
                                overall_effectiveness_code = EXCLUDED.overall_effectiveness_code,
                                overall_effectiveness_label = EXCLUDED.overall_effectiveness_label,
                                headline_outcome_text = EXCLUDED.headline_outcome_text,
                                category_of_concern = EXCLUDED.category_of_concern,
                                source_schema_version = EXCLUDED.source_schema_version,
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
        return f"ofsted_timeline__{context.run_id.hex}"

    def _resolve_assets(self) -> list[OfstedTimelineAsset]:
        if self._source_assets_csv:
            asset_urls = _parse_source_assets_csv(self._source_assets_csv)
            if not asset_urls:
                raise ValueError(
                    "CIVITAS_OFSTED_TIMELINE_SOURCE_ASSETS did not include any asset URLs."
                )
            return [_asset_from_source(asset_url) for asset_url in asset_urls]

        landing_page_html = _download_text(self._source_index_url)
        all_inspections_url, _, historical_url = extract_ofsted_timeline_asset_urls(
            landing_page_html
        )

        assets = [_asset_from_source(all_inspections_url)]
        if self._include_historical_baseline:
            if historical_url is None:
                raise ValueError(
                    "Historical Ofsted baseline asset (2015-2019) was not found on landing page."
                )
            assets.append(_asset_from_source(historical_url))

        return assets


def _asset_from_source(source_asset_url: str) -> OfstedTimelineAsset:
    lowered = source_asset_url.casefold()
    if _HISTORICAL_ASSET_TOKEN in lowered:
        schema_hint = SCHEMA_VERSION_HISTORICAL_2015_2019
    else:
        schema_hint = SCHEMA_VERSION_YTD
    return OfstedTimelineAsset(
        source_asset_url=source_asset_url,
        source_schema_hint=schema_hint,
        source_asset_month=_infer_source_asset_month(source_asset_url),
    )


def _parse_source_assets_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _build_bronze_asset_file_name(source_asset_url: str, *, index: int) -> str:
    parsed = urllib.parse.urlparse(source_asset_url)
    candidate = Path(parsed.path).name if parsed.path else ""
    if not candidate:
        candidate = f"asset_{index:02d}.csv"
    elif not candidate.casefold().endswith(".csv"):
        candidate = f"{candidate}.csv"
    return f"{index:02d}_{candidate}"


def _read_csv_rows(
    csv_path: Path,
    *,
    schema_hint: str,
) -> tuple[list[str], list[dict[str, str]], str]:
    raw_bytes = csv_path.read_bytes()
    last_decode_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            csv_text = raw_bytes.decode(encoding)
        except UnicodeDecodeError as exc:
            last_decode_error = exc
            continue

        rows = list(csv.reader(io.StringIO(csv_text, newline="")))
        if not rows:
            raise ValueError(f"Ofsted timeline CSV '{csv_path}' has no rows.")

        header_index = _detect_header_index(rows)
        headers = [_clean_header_value(value) for value in rows[header_index]]
        schema_version = _detect_schema_version(
            headers, header_index=header_index, schema_hint=schema_hint
        )

        data_rows: list[dict[str, str]] = []
        for row in rows[header_index + 1 :]:
            if not any(cell.strip() for cell in row):
                continue
            normalized_row = list(row)
            if len(normalized_row) < len(headers):
                normalized_row.extend([""] * (len(headers) - len(normalized_row)))
            elif len(normalized_row) > len(headers):
                normalized_row = normalized_row[: len(headers)]
            data_rows.append(dict(zip(headers, normalized_row, strict=True)))

        return headers, data_rows, schema_version

    if last_decode_error is not None:
        raise last_decode_error
    raise ValueError(f"Unable to decode Ofsted timeline CSV at '{csv_path}'.")


def _detect_header_index(rows: list[list[str]]) -> int:
    if rows and _looks_like_timeline_header(rows[0]):
        return 0
    if len(rows) > 1 and _looks_like_timeline_header(rows[1]):
        return 1
    raise ValueError("Ofsted timeline CSV header could not be detected.")


def _looks_like_timeline_header(row: list[str]) -> bool:
    normalized = {_clean_header_value(value) for value in row}
    return "URN" in normalized and "Inspection number" in normalized


def _detect_schema_version(headers: Sequence[str], *, header_index: int, schema_hint: str) -> str:
    if "Academic year" in headers:
        return SCHEMA_VERSION_HISTORICAL_2015_2019
    if header_index == 1:
        return SCHEMA_VERSION_HISTORICAL_2015_2019
    if schema_hint == SCHEMA_VERSION_HISTORICAL_2015_2019:
        return SCHEMA_VERSION_HISTORICAL_2015_2019
    return SCHEMA_VERSION_YTD


def _normalize_overall_effectiveness_code(raw_value: str) -> str | None:
    value = raw_value.strip()
    if not value:
        return None
    if value.casefold() == "not judged":
        return "Not judged"
    if value in {"1", "2", "3", "4"}:
        return value

    with suppress(ValueError):
        numeric_value = float(value)
        if numeric_value in {1.0, 2.0, 3.0, 4.0} and numeric_value.is_integer():
            return str(int(numeric_value))

    mapped = OVERALL_EFFECTIVENESS_LABEL_TO_CODE.get(value.casefold())
    if mapped is not None:
        return mapped
    return None


def _is_more_recent_timeline_row(
    candidate: OfstedTimelineStagedRow,
    existing: OfstedTimelineStagedRow,
) -> bool:
    candidate_key = (
        candidate.inspection_start_date,
        candidate.publication_date or date.min,
        candidate.source_asset_month or "",
        candidate.source_schema_version,
        candidate.source_asset_url,
    )
    existing_key = (
        existing.inspection_start_date,
        existing.publication_date or date.min,
        existing.source_asset_month or "",
        existing.source_schema_version,
        existing.source_asset_url,
    )
    return candidate_key > existing_key


def _infer_source_asset_month(source_asset_url: str | None) -> str | None:
    if source_asset_url is None:
        return None
    match = _ASSET_DATE_PATTERN.search(source_asset_url)
    if match is None:
        return None

    month_token = match.group("month").strip().casefold()
    month_number = _MONTH_ABBR_TO_NUMBER.get(month_token)
    if month_number is None:
        return None
    year = int(match.group("year"))
    return f"{year:04d}-{month_number:02d}"


def _select_latest_dated_asset_url(candidates: Sequence[str]) -> str | None:
    ranked_candidates: list[tuple[tuple[int, int, int], str]] = []
    for candidate in candidates:
        sort_key = _asset_sort_date(candidate)
        ranked_candidates.append((sort_key, candidate))
    if not ranked_candidates:
        return None
    ranked_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return ranked_candidates[0][1]


def _asset_sort_date(source_asset_url: str) -> tuple[int, int, int]:
    match = _ASSET_DATE_PATTERN.search(source_asset_url)
    if match is None:
        return (0, 0, 0)
    month_token = match.group("month").strip().casefold()
    month_number = _MONTH_ABBR_TO_NUMBER.get(month_token)
    if month_number is None:
        return (0, 0, 0)
    year = int(match.group("year"))
    day = int(match.group("day"))
    return (year, month_number, day)


def _normalize_asset_href(raw_href: str) -> str | None:
    if not raw_href:
        return None
    if raw_href.startswith("//assets.publishing.service.gov.uk/"):
        return f"https:{raw_href}"
    if raw_href.startswith(_ASSET_URL_PREFIX):
        return raw_href
    return None


def _parse_required_date(raw_value: str | None) -> date:
    value = (raw_value or "").strip()
    if not value:
        raise ValueError("missing required date")
    parsed = _parse_optional_date(value)
    if parsed is None:
        raise ValueError("missing required date")
    return parsed


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


def _first_non_empty(raw_row: Mapping[str, str], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = _strip_or_none(raw_row.get(key))
        if value is not None:
            return value
    return None


def _strip_or_none(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    return value or None


def _normalize_month(raw_month: str | None) -> str | None:
    value = (raw_month or "").strip()
    if not value:
        return None
    if len(value) == 7 and value[4] == "-" and value[:4].isdigit() and value[5:].isdigit():
        return value
    return None


def _clean_header_value(value: str) -> str:
    return value.strip().lstrip("\ufeff")


def _count_csv_rows(csv_path: Path, *, schema_hint: str) -> int:
    _, rows, _ = _read_csv_rows(csv_path, schema_hint=schema_hint)
    return len(rows)


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
        raise FileNotFoundError(f"Configured Ofsted timeline source '{source_path}' was not found.")
    shutil.copy2(source_path, target)


def _load_manifest(manifest_path: Path) -> dict[str, object]:
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _manifest_assets(manifest: dict[str, object]) -> list[dict[str, object]]:
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        return []
    normalized_assets: list[dict[str, object]] = []
    for asset in assets:
        if isinstance(asset, dict) and isinstance(asset.get("bronze_file_name"), str):
            normalized_assets.append(asset)
    return normalized_assets


def _manifest_asset_file_name(asset: dict[str, object]) -> str | None:
    value = asset.get("bronze_file_name")
    if isinstance(value, str) and value:
        return value
    return None


def _manifest_asset_row_count(asset: dict[str, object]) -> int:
    value = asset.get("rows")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        with suppress(ValueError):
            return int(value)
    return 0


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
