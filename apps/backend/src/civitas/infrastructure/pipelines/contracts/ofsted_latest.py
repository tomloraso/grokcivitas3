from __future__ import annotations

from contextlib import suppress
from datetime import date, datetime
from typing import Mapping, Sequence, TypedDict
from urllib.parse import urlparse, urlunparse

CONTRACT_VERSION = "ofsted_latest.v4"

REQUIRED_HEADERS: tuple[str, ...] = (
    "URN",
    "Web Link (opens in new window)",
    "Inspection start date",
    "Publication date",
    "Latest OEIF overall effectiveness",
    "Inspection start date of latest OEIF graded inspection",
    "Publication date of latest OEIF graded inspection",
    "Latest OEIF quality of education",
    "Latest OEIF behaviour and attitudes",
    "Latest OEIF personal development",
    "Latest OEIF effectiveness of leadership and management",
    "Date of latest ungraded inspection",
    "Ungraded inspection publication date",
    "Ungraded inspection overall outcome",
)

NULL_TOKENS: set[str] = {"", "NULL", "N/A", "NA"}

JUDGEMENT_CODE_TO_LABEL: dict[str, str] = {
    "1": "Outstanding",
    "2": "Good",
    "3": "Requires improvement",
    "4": "Inadequate",
    "Not judged": "Not judged",
}


class NormalizedOfstedLatestRow(TypedDict):
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
        provider_page_url = parse_provider_page_url(raw_row["Web Link (opens in new window)"])
    except ValueError as exc:
        rejection_code = str(exc)
        return None, rejection_code

    try:
        inspection_start_date = parse_optional_date(raw_row["Inspection start date"])
    except ValueError:
        return None, "invalid_inspection_start_date"

    try:
        publication_date = parse_optional_date(raw_row["Publication date"])
    except ValueError:
        return None, "invalid_publication_date"

    try:
        latest_oeif_inspection_start_date = parse_optional_date(
            raw_row["Inspection start date of latest OEIF graded inspection"]
        )
    except ValueError:
        return None, "invalid_latest_oeif_inspection_start_date"

    try:
        latest_oeif_publication_date = parse_optional_date(
            raw_row["Publication date of latest OEIF graded inspection"]
        )
    except ValueError:
        return None, "invalid_latest_oeif_publication_date"

    try:
        latest_ungraded_inspection_date = parse_optional_date(
            raw_row["Date of latest ungraded inspection"]
        )
    except ValueError:
        return None, "invalid_latest_ungraded_inspection_date"

    try:
        latest_ungraded_publication_date = parse_optional_date(
            raw_row["Ungraded inspection publication date"]
        )
    except ValueError:
        return None, "invalid_latest_ungraded_publication_date"

    overall_effectiveness_raw = strip_or_none(raw_row["Latest OEIF overall effectiveness"])
    overall_effectiveness_code: str | None = None
    overall_effectiveness_label: str | None = None
    is_graded = False

    if overall_effectiveness_raw is not None:
        normalized_code = normalize_judgement_code(overall_effectiveness_raw)
        if normalized_code is not None:
            if normalized_code not in JUDGEMENT_CODE_TO_LABEL:
                return None, "invalid_overall_effectiveness_code"
            overall_effectiveness_code = normalized_code
            overall_effectiveness_label = JUDGEMENT_CODE_TO_LABEL[normalized_code]
            is_graded = normalized_code in {"1", "2", "3", "4"}

    quality_of_education_code, quality_of_education_label, quality_rejection = _parse_sub_judgement(
        raw_row,
        header="Latest OEIF quality of education",
        rejection_code="invalid_quality_of_education_code",
    )
    if quality_rejection is not None:
        return None, quality_rejection

    behaviour_and_attitudes_code, behaviour_and_attitudes_label, behaviour_rejection = (
        _parse_sub_judgement(
            raw_row,
            header="Latest OEIF behaviour and attitudes",
            rejection_code="invalid_behaviour_and_attitudes_code",
        )
    )
    if behaviour_rejection is not None:
        return None, behaviour_rejection

    personal_development_code, personal_development_label, personal_dev_rejection = (
        _parse_sub_judgement(
            raw_row,
            header="Latest OEIF personal development",
            rejection_code="invalid_personal_development_code",
        )
    )
    if personal_dev_rejection is not None:
        return None, personal_dev_rejection

    leadership_and_management_code, leadership_and_management_label, leadership_rejection = (
        _parse_sub_judgement(
            raw_row,
            header="Latest OEIF effectiveness of leadership and management",
            rejection_code="invalid_leadership_and_management_code",
        )
    )
    if leadership_rejection is not None:
        return None, leadership_rejection

    return (
        NormalizedOfstedLatestRow(
            urn=urn,
            provider_page_url=provider_page_url,
            inspection_start_date=inspection_start_date,
            publication_date=publication_date,
            overall_effectiveness_code=overall_effectiveness_code,
            overall_effectiveness_label=overall_effectiveness_label,
            latest_oeif_inspection_start_date=latest_oeif_inspection_start_date,
            latest_oeif_publication_date=latest_oeif_publication_date,
            quality_of_education_code=quality_of_education_code,
            quality_of_education_label=quality_of_education_label,
            behaviour_and_attitudes_code=behaviour_and_attitudes_code,
            behaviour_and_attitudes_label=behaviour_and_attitudes_label,
            personal_development_code=personal_development_code,
            personal_development_label=personal_development_label,
            leadership_and_management_code=leadership_and_management_code,
            leadership_and_management_label=leadership_and_management_label,
            latest_ungraded_inspection_date=latest_ungraded_inspection_date,
            latest_ungraded_publication_date=latest_ungraded_publication_date,
            is_graded=is_graded,
            ungraded_outcome=strip_or_none(raw_row["Ungraded inspection overall outcome"]),
            source_asset_url=source_asset_url,
            source_asset_month=source_asset_month,
        ),
        None,
    )


def normalize_judgement_code(raw_value: str) -> str | None:
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


def parse_provider_page_url(raw_value: str | None) -> str:
    value = strip_or_none(raw_value)
    if value is None:
        raise ValueError("missing_provider_page_url")

    parsed = urlparse(value)
    host = parsed.netloc.casefold()
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("invalid_provider_page_url")
    if host not in {"www.ofsted.gov.uk", "ofsted.gov.uk", "reports.ofsted.gov.uk"}:
        raise ValueError("invalid_provider_page_url")
    if not (
        parsed.path.startswith("/inspection-reports/find-inspection-report/provider/")
        or parsed.path.startswith("/provider/")
    ):
        raise ValueError("invalid_provider_page_url")

    normalized_host = host
    if host in {"www.ofsted.gov.uk", "ofsted.gov.uk"}:
        normalized_host = "reports.ofsted.gov.uk"

    normalized = parsed._replace(scheme="https", netloc=normalized_host)
    return urlunparse(normalized)


def _parse_sub_judgement(
    raw_row: Mapping[str, str],
    *,
    header: str,
    rejection_code: str,
) -> tuple[str | None, str | None, str | None]:
    raw_value = strip_or_none(raw_row.get(header))
    if raw_value is None:
        return None, None, None

    normalized_code = normalize_judgement_code(raw_value)
    if normalized_code is None or normalized_code not in JUDGEMENT_CODE_TO_LABEL:
        return None, None, rejection_code
    return normalized_code, JUDGEMENT_CODE_TO_LABEL[normalized_code], None


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
