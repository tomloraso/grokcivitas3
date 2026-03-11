from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TypedDict

CONTRACT_VERSION = "ks4_subject_performance.v1"

MEASURE_NULL_TOKENS: set[str] = {
    "",
    ".",
    "supp",
    "suppressed",
    "n/a",
    "na",
    "x",
    "z",
    "c",
    "u",
}

KS4_REQUIRED_HEADERS: tuple[str, ...] = (
    "time_period",
    "time_identifier",
    "geographic_level",
    "country_code",
    "country_name",
    "school_laestab",
    "school_urn",
    "school_name",
    "old_la_code",
    "new_la_code",
    "la_name",
    "version",
    "establishment_type_group",
    "pupil_count",
    "qualification_type",
    "qualification_detailed",
    "grade_structure",
    "subject",
    "discount_code",
    "subject_discount_group",
    "grade",
    "number_achieving",
)


class NormalizedKs4SubjectPerformanceRow(TypedDict):
    academic_year: str
    school_urn: str
    school_laestab: str | None
    school_name: str
    old_la_code: str | None
    new_la_code: str | None
    la_name: str | None
    source_version: str
    establishment_type_group: str | None
    pupil_count: int | None
    qualification_type: str
    qualification_family: str
    qualification_detailed: str | None
    grade_structure: str
    subject: str
    discount_code: str | None
    subject_discount_group: str | None
    grade: str
    number_achieving: int | None
    source_file_url: str


def validate_headers(headers: list[str] | tuple[str, ...]) -> None:
    normalized_headers = tuple(str(header).strip() for header in headers)
    if normalized_headers == KS4_REQUIRED_HEADERS:
        return

    missing = [header for header in KS4_REQUIRED_HEADERS if header not in normalized_headers]
    unexpected = [header for header in normalized_headers if header not in KS4_REQUIRED_HEADERS]
    details: list[str] = []
    if missing:
        details.append("missing headers: " + ", ".join(missing))
    if unexpected:
        details.append("unexpected headers: " + ", ".join(unexpected))
    if not missing and not unexpected:
        details.append("header order changed")
    raise ValueError("KS4 subject performance schema mismatch; " + "; ".join(details))


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    source_file_url: str,
) -> tuple[NormalizedKs4SubjectPerformanceRow | None, str | None]:
    try:
        academic_year = parse_academic_year(raw_row.get("time_period"))
    except ValueError:
        return None, "invalid_academic_year"

    time_identifier = parse_optional_text(raw_row.get("time_identifier"))
    if time_identifier is not None and time_identifier.casefold() != "academic year":
        return None, "unsupported_time_identifier"

    geographic_level = parse_optional_text(raw_row.get("geographic_level"))
    if geographic_level is not None and geographic_level.casefold() != "school":
        return None, "unsupported_geographic_level"

    school_urn = parse_optional_text(raw_row.get("school_urn"))
    if school_urn is None or len(school_urn) != 6 or not school_urn.isdigit():
        return None, "invalid_school_urn"

    school_name = parse_optional_text(raw_row.get("school_name"))
    if school_name is None:
        return None, "missing_school_name"

    school_laestab = parse_optional_text(raw_row.get("school_laestab"))
    if school_laestab is not None and not school_laestab.isdigit():
        return None, "invalid_school_laestab"

    qualification_type = parse_optional_text(raw_row.get("qualification_type"))
    if qualification_type is None:
        return None, "missing_qualification_type"

    grade_structure = parse_optional_text(raw_row.get("grade_structure"))
    if grade_structure is None:
        return None, "missing_grade_structure"

    subject = parse_optional_text(raw_row.get("subject"))
    if subject is None:
        return None, "missing_subject"

    grade = parse_optional_text(raw_row.get("grade"))
    if grade is None:
        return None, "missing_grade"

    try:
        pupil_count = parse_optional_integer(raw_row.get("pupil_count"), min_value=0)
        number_achieving = parse_optional_integer(raw_row.get("number_achieving"), min_value=0)
    except ValueError as exc:
        return None, str(exc)

    return (
        NormalizedKs4SubjectPerformanceRow(
            academic_year=academic_year,
            school_urn=school_urn,
            school_laestab=school_laestab,
            school_name=school_name,
            old_la_code=parse_optional_text(raw_row.get("old_la_code")),
            new_la_code=parse_optional_text(raw_row.get("new_la_code")),
            la_name=parse_optional_text(raw_row.get("la_name")),
            source_version=normalize_source_version(raw_row.get("version")),
            establishment_type_group=parse_optional_text(raw_row.get("establishment_type_group")),
            pupil_count=pupil_count,
            qualification_type=qualification_type,
            qualification_family=normalize_ks4_qualification_family(qualification_type),
            qualification_detailed=parse_optional_text(raw_row.get("qualification_detailed")),
            grade_structure=grade_structure,
            subject=subject,
            discount_code=parse_optional_text(raw_row.get("discount_code")),
            subject_discount_group=parse_optional_text(raw_row.get("subject_discount_group")),
            grade=grade,
            number_achieving=number_achieving,
            source_file_url=source_file_url,
        ),
        None,
    )


def parse_academic_year(raw_value: str | None) -> str:
    value = parse_optional_text(raw_value)
    if value is None or len(value) != 6 or not value.isdigit():
        raise ValueError("invalid_academic_year")
    return f"{value[:4]}/{value[4:]}"


def normalize_source_version(raw_value: object) -> str:
    value = parse_optional_text(raw_value)
    if value is None:
        return "unknown"
    normalized = value.casefold()
    if normalized in {"final", "revised", "provisional"}:
        return normalized
    return normalized or "unknown"


def normalize_ks4_qualification_family(raw_value: object) -> str:
    value = parse_optional_text(raw_value)
    if value is None:
        return "unknown"
    normalized = value.casefold().replace("&", "and")
    if normalized == "gcse":
        return "gcse"
    if normalized == "vocational":
        return "vocational"
    if normalized == "as level":
        return "as_level"
    if normalized == "fsmq":
        return "fsmq"
    if "performing arts" in normalized:
        return "performing_arts_grade"
    slug = "".join(character if character.isalnum() else "_" for character in normalized)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "unknown"


def parse_optional_integer(
    raw_value: object,
    *,
    min_value: int | None = None,
) -> int | None:
    value = parse_optional_measure_text(raw_value)
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError("invalid_integer") from exc
    if min_value is not None and parsed < min_value:
        raise ValueError("invalid_integer")
    return parsed


def parse_optional_measure_text(raw_value: object) -> str | None:
    if raw_value is None:
        return None
    token = str(raw_value).strip()
    if token.casefold() in MEASURE_NULL_TOKENS:
        return None
    return token or None


def parse_optional_text(raw_value: object) -> str | None:
    if raw_value is None:
        return None
    token = str(raw_value).strip()
    return token or None


def parse_optional_decimal(raw_value: object) -> float | None:
    value = parse_optional_measure_text(raw_value)
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError("invalid_float") from exc
    if not math.isfinite(parsed):
        raise ValueError("invalid_float")
    return parsed
