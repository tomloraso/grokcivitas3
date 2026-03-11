from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TypedDict

CONTRACT_VERSION = "sixteen_to_eighteen_subject_performance.v1"

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

REQUIRED_HEADERS: tuple[str, ...] = (
    "time_period",
    "time_identifier",
    "geographic_level",
    "country_code",
    "country_name",
    "version",
    "old_la_code",
    "new_la_code",
    "la_name",
    "school_name",
    "school_urn",
    "school_laestab",
    "exam_cohort",
    "qualification_detailed",
    "qualification_level",
    "a_level_equivelent_size",
    "gcse_equivelent_size",
    "grade_structure",
    "subject",
    "grade",
    "entries_count",
)


class NormalizedSixteenToEighteenSubjectPerformanceRow(TypedDict):
    academic_year: str
    school_urn: str
    school_laestab: str | None
    school_name: str
    old_la_code: str | None
    new_la_code: str | None
    la_name: str | None
    source_version: str
    exam_cohort: str
    qualification_detailed: str
    qualification_family: str
    qualification_level: str | None
    a_level_equivalent_size: float | None
    gcse_equivalent_size: float | None
    grade_structure: str
    subject: str
    grade: str
    entries_count: int | None
    source_file_url: str


def validate_headers(headers: list[str] | tuple[str, ...]) -> None:
    normalized_headers = tuple(str(header).strip() for header in headers)
    if normalized_headers == REQUIRED_HEADERS:
        return

    missing = [header for header in REQUIRED_HEADERS if header not in normalized_headers]
    unexpected = [header for header in normalized_headers if header not in REQUIRED_HEADERS]
    details: list[str] = []
    if missing:
        details.append("missing headers: " + ", ".join(missing))
    if unexpected:
        details.append("unexpected headers: " + ", ".join(unexpected))
    if not missing and not unexpected:
        details.append("header order changed")
    raise ValueError("16 to 18 subject performance schema mismatch; " + "; ".join(details))


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    source_file_url: str,
) -> tuple[NormalizedSixteenToEighteenSubjectPerformanceRow | None, str | None]:
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

    exam_cohort = parse_optional_text(raw_row.get("exam_cohort"))
    if exam_cohort is None:
        return None, "missing_exam_cohort"

    qualification_detailed = parse_optional_text(raw_row.get("qualification_detailed"))
    if qualification_detailed is None:
        return None, "missing_qualification_detailed"

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
        a_level_equivalent_size = parse_optional_decimal(raw_row.get("a_level_equivelent_size"))
        gcse_equivalent_size = parse_optional_decimal(raw_row.get("gcse_equivelent_size"))
        entries_count = parse_optional_integer(raw_row.get("entries_count"), min_value=0)
    except ValueError as exc:
        return None, str(exc)

    return (
        NormalizedSixteenToEighteenSubjectPerformanceRow(
            academic_year=academic_year,
            school_urn=school_urn,
            school_laestab=school_laestab,
            school_name=school_name,
            old_la_code=parse_optional_text(raw_row.get("old_la_code")),
            new_la_code=parse_optional_text(raw_row.get("new_la_code")),
            la_name=parse_optional_text(raw_row.get("la_name")),
            source_version=normalize_source_version(raw_row.get("version")),
            exam_cohort=exam_cohort,
            qualification_detailed=qualification_detailed,
            qualification_family=normalize_qualification_family(
                exam_cohort=exam_cohort,
                qualification_detailed=qualification_detailed,
            ),
            qualification_level=parse_optional_text(raw_row.get("qualification_level")),
            a_level_equivalent_size=a_level_equivalent_size,
            gcse_equivalent_size=gcse_equivalent_size,
            grade_structure=grade_structure,
            subject=subject,
            grade=grade,
            entries_count=entries_count,
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


def normalize_qualification_family(
    *,
    exam_cohort: str,
    qualification_detailed: str,
) -> str:
    exam_cohort_value = exam_cohort.casefold()
    qualification_value = qualification_detailed.casefold()
    if "gce a level" in qualification_value or exam_cohort_value == "a level":
        return "a_level"
    if "gce as level" in qualification_value or exam_cohort_value == "as level":
        return "as_level"
    if "btec" in qualification_value:
        return "btec"
    if "cambridge technical" in qualification_value:
        return "cambridge_technical"
    if "international baccalaureate" in qualification_value or qualification_value == "ibo diploma":
        return "international_baccalaureate"
    slug = "".join(character if character.isalnum() else "_" for character in exam_cohort_value)
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
