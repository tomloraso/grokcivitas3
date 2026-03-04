from __future__ import annotations

from contextlib import suppress
from datetime import date, datetime
from typing import Mapping, Sequence, TypedDict

CONTRACT_VERSION = "ofsted_latest.v1"

REQUIRED_HEADERS: tuple[str, ...] = (
    "URN",
    "Inspection start date",
    "Publication date",
    "Latest OEIF overall effectiveness",
    "Ungraded inspection overall outcome",
)

NULL_TOKENS: set[str] = {"", "NULL", "N/A", "NA"}

OVERALL_EFFECTIVENESS_CODE_TO_LABEL: dict[str, str] = {
    "1": "Outstanding",
    "2": "Good",
    "3": "Requires improvement",
    "4": "Inadequate",
    "Not judged": "Not judged",
}


class NormalizedOfstedLatestRow(TypedDict):
    urn: str
    inspection_start_date: date | None
    publication_date: date | None
    overall_effectiveness_code: str | None
    overall_effectiveness_label: str | None
    is_graded: bool
    ungraded_outcome: str | None
    source_asset_url: str
    source_asset_month: str | None


def validate_headers(headers: Sequence[str]) -> None:
    header_set = set(headers)
    missing = [header for header in REQUIRED_HEADERS if header not in header_set]
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(
            f"Ofsted latest schema mismatch; missing required headers: {missing_fields}"
        )


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    source_asset_url: str,
    source_asset_month: str | None,
) -> tuple[NormalizedOfstedLatestRow | None, str | None]:
    urn = raw_row["URN"].strip()
    if not urn:
        return None, "missing_urn"

    try:
        inspection_start_date = parse_optional_date(raw_row["Inspection start date"])
    except ValueError:
        return None, "invalid_inspection_start_date"

    try:
        publication_date = parse_optional_date(raw_row["Publication date"])
    except ValueError:
        return None, "invalid_publication_date"

    overall_effectiveness_raw = strip_or_none(raw_row["Latest OEIF overall effectiveness"])
    overall_effectiveness_code: str | None = None
    overall_effectiveness_label: str | None = None
    is_graded = False

    if overall_effectiveness_raw is not None:
        normalized_code = normalize_overall_effectiveness_code(overall_effectiveness_raw)
        if normalized_code is not None:
            if normalized_code not in OVERALL_EFFECTIVENESS_CODE_TO_LABEL:
                return None, "invalid_overall_effectiveness_code"
            overall_effectiveness_code = normalized_code
            overall_effectiveness_label = OVERALL_EFFECTIVENESS_CODE_TO_LABEL[normalized_code]
            is_graded = normalized_code in {"1", "2", "3", "4"}

    return (
        NormalizedOfstedLatestRow(
            urn=urn,
            inspection_start_date=inspection_start_date,
            publication_date=publication_date,
            overall_effectiveness_code=overall_effectiveness_code,
            overall_effectiveness_label=overall_effectiveness_label,
            is_graded=is_graded,
            ungraded_outcome=strip_or_none(raw_row["Ungraded inspection overall outcome"]),
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

    with suppress(ValueError):
        numeric_value = float(value)
        if numeric_value == 9.0:
            return "Not judged"
        if numeric_value in {1.0, 2.0, 3.0, 4.0} and numeric_value.is_integer():
            return str(int(numeric_value))

    if value in {"1", "2", "3", "4"}:
        return value

    return value


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


def strip_or_none(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    if value.upper() in NULL_TOKENS:
        return None
    return value or None
