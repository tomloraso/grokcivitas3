from __future__ import annotations

from contextlib import suppress
from datetime import date, datetime
from typing import Mapping, Sequence, TypedDict

CONTRACT_VERSION = "ofsted_timeline.v1"

SCHEMA_VERSION_YTD = "all_inspections_ytd"
SCHEMA_VERSION_HISTORICAL_2015_2019 = "all_inspections_historical_2015_2019"

SUPPORTED_SCHEMA_VERSIONS: tuple[str, ...] = (
    SCHEMA_VERSION_YTD,
    SCHEMA_VERSION_HISTORICAL_2015_2019,
)

REQUIRED_HEADERS_YTD: tuple[str, ...] = (
    "URN",
    "Inspection number",
    "Inspection type",
    "Inspection start date",
    "Publication date",
)

REQUIRED_HEADERS_HISTORICAL: tuple[str, ...] = (
    "Academic year",
    "URN",
    "Inspection number",
    "Inspection start date",
    "Publication date",
    "Overall effectiveness",
)

NULL_TOKENS: set[str] = {"", "NULL", "N/A", "NA"}

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


class NormalizedOfstedTimelineRow(TypedDict):
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


def validate_headers(headers: Sequence[str], *, schema_version: str) -> None:
    required_headers = (
        REQUIRED_HEADERS_HISTORICAL
        if schema_version == SCHEMA_VERSION_HISTORICAL_2015_2019
        else REQUIRED_HEADERS_YTD
    )
    header_set = set(headers)
    missing = [header for header in required_headers if header not in header_set]
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(
            f"Ofsted timeline schema mismatch for '{schema_version}'; "
            f"missing required headers: {missing_fields}"
        )


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    source_schema_version: str,
    source_asset_url: str,
    source_asset_month: str | None,
) -> tuple[NormalizedOfstedTimelineRow | None, str | None]:
    urn = strip_or_none(raw_row.get("URN"))
    if urn is None:
        return None, "missing_urn"

    inspection_number = strip_or_none(raw_row.get("Inspection number"))
    if inspection_number is None:
        return None, "missing_inspection_number"

    inspection_start_raw = raw_row.get("Inspection start date")
    try:
        inspection_start_date = parse_required_date(inspection_start_raw)
    except ValueError:
        return None, "invalid_inspection_start_date"

    try:
        inspection_end_date = parse_optional_date(raw_row.get("Inspection end date"))
    except ValueError:
        return None, "invalid_inspection_end_date"

    try:
        publication_date = parse_optional_date(raw_row.get("Publication date"))
    except ValueError:
        return None, "invalid_publication_date"

    overall_effectiveness_raw = first_non_empty(
        raw_row,
        [
            "Latest OEIF overall effectiveness",
            "Overall effectiveness",
        ],
    )
    overall_effectiveness_code: str | None = None
    overall_effectiveness_label: str | None = None
    if overall_effectiveness_raw is not None:
        overall_effectiveness_code = normalize_overall_effectiveness_code(overall_effectiveness_raw)
        if overall_effectiveness_code is not None:
            overall_effectiveness_label = OVERALL_EFFECTIVENESS_CODE_TO_LABEL[
                overall_effectiveness_code
            ]

    headline_outcome_text = first_non_empty(
        raw_row,
        [
            "Ungraded inspection overall outcome",
            "Outcome",
        ],
    )
    if headline_outcome_text is None and overall_effectiveness_code is None:
        headline_outcome_text = overall_effectiveness_raw

    return (
        NormalizedOfstedTimelineRow(
            inspection_number=inspection_number,
            urn=urn,
            inspection_start_date=inspection_start_date,
            inspection_end_date=inspection_end_date,
            publication_date=publication_date,
            inspection_type=first_non_empty(raw_row, ["Inspection type"]),
            inspection_type_grouping=first_non_empty(raw_row, ["Inspection type grouping"]),
            event_type_grouping=first_non_empty(raw_row, ["Event type grouping"]),
            overall_effectiveness_code=overall_effectiveness_code,
            overall_effectiveness_label=overall_effectiveness_label,
            headline_outcome_text=headline_outcome_text,
            category_of_concern=first_non_empty(raw_row, ["Category of concern"]),
            source_schema_version=source_schema_version,
            source_asset_url=source_asset_url,
            source_asset_month=source_asset_month,
        ),
        None,
    )


def normalize_overall_effectiveness_code(raw_value: str) -> str | None:
    value = raw_value.strip()
    if value.upper() in NULL_TOKENS:
        return None
    if value.casefold() == "not judged":
        return "Not judged"
    if value in {"1", "2", "3", "4"}:
        return value

    with suppress(ValueError):
        numeric_value = float(value)
        if numeric_value == 9.0:
            return "Not judged"
        if numeric_value in {1.0, 2.0, 3.0, 4.0} and numeric_value.is_integer():
            return str(int(numeric_value))

    mapped = OVERALL_EFFECTIVENESS_LABEL_TO_CODE.get(value.casefold())
    if mapped is not None:
        return mapped
    return None


def parse_required_date(raw_value: str | None) -> date:
    value = (raw_value or "").strip()
    if not value:
        raise ValueError("missing required date")
    parsed = parse_optional_date(value)
    if parsed is None:
        raise ValueError("missing required date")
    return parsed


def parse_optional_date(raw_value: str | None) -> date | None:
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


def first_non_empty(raw_row: Mapping[str, str], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = strip_or_none(raw_row.get(key))
        if value is not None:
            return value
    return None


def strip_or_none(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    if value.upper() in NULL_TOKENS:
        return None
    return value or None
