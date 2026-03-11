from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Literal, TypedDict

CONTRACT_VERSION = "leaver_destinations.v1"

DestinationStage = Literal["ks4", "16_to_18"]
DestinationDataType = Literal["Number of students", "Percentage"]

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
    "region_code",
    "region_name",
    "old_la_code",
    "new_la_code",
    "la_name",
    "local_authority_selection_status",
    "school_laestab",
    "school_urn",
    "school_name",
    "admission_policy",
    "entry_gender",
    "institution_group",
    "institution_type",
    "breakdown_topic",
    "breakdown",
    "data_type",
    "version",
    "cohort",
    "overall",
    "education",
    "fe",
    "ssf",
    "sfc",
    "other_edu",
    "appren",
    "all_work",
    "all_notsust",
    "all_unknown",
)

STUDY_16_TO_18_REQUIRED_HEADERS: tuple[str, ...] = (
    "time_period",
    "time_identifier",
    "geographic_level",
    "country_code",
    "country_name",
    "region_code",
    "region_name",
    "old_la_code",
    "new_la_code",
    "la_name",
    "local_authority_selection_status",
    "school_laestab",
    "school_urn",
    "school_name",
    "admission_policy",
    "entry_gender",
    "institution_group",
    "institution_type",
    "cohort_level_group",
    "cohort_level",
    "breakdown_topic",
    "breakdown",
    "data_type",
    "version",
    "cohort",
    "overall",
    "education",
    "he",
    "fe",
    "other_edu",
    "appren",
    "all_work",
    "all_notsust",
    "all_unknown",
)


class NormalizedLeaverDestinationsRow(TypedDict):
    academic_year: str
    destination_stage: DestinationStage
    school_urn: str
    school_laestab: str | None
    school_name: str
    admission_policy: str | None
    entry_gender: str | None
    institution_group: str | None
    institution_type: str | None
    qualification_group: str | None
    qualification_level: str | None
    breakdown_topic: str
    breakdown: str
    data_type: DestinationDataType
    cohort_count: int | None
    overall_value: float | None
    education_value: float | None
    apprenticeship_value: float | None
    employment_value: float | None
    not_sustained_value: float | None
    activity_unknown_value: float | None
    fe_value: float | None
    other_education_value: float | None
    school_sixth_form_value: float | None
    sixth_form_college_value: float | None
    higher_education_value: float | None
    source_file_url: str


def validate_headers(
    *,
    destination_stage: DestinationStage,
    headers: list[str] | tuple[str, ...],
) -> None:
    required_headers = (
        KS4_REQUIRED_HEADERS if destination_stage == "ks4" else STUDY_16_TO_18_REQUIRED_HEADERS
    )
    normalized_headers = tuple(str(header).strip() for header in headers)
    if normalized_headers == required_headers:
        return

    missing = [header for header in required_headers if header not in normalized_headers]
    unexpected = [header for header in normalized_headers if header not in required_headers]
    details: list[str] = []
    if missing:
        details.append("missing headers: " + ", ".join(missing))
    if unexpected:
        details.append("unexpected headers: " + ", ".join(unexpected))
    if not missing and not unexpected:
        details.append("header order changed")
    raise ValueError("Leaver destinations schema mismatch; " + "; ".join(details))


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    destination_stage: DestinationStage,
    source_file_url: str,
) -> tuple[NormalizedLeaverDestinationsRow | None, str | None]:
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

    breakdown_topic = parse_optional_text(raw_row.get("breakdown_topic"))
    if breakdown_topic is None:
        return None, "missing_breakdown_topic"

    breakdown = parse_optional_text(raw_row.get("breakdown"))
    if breakdown is None:
        return None, "missing_breakdown"

    try:
        data_type = parse_data_type(raw_row.get("data_type"))
        cohort_count = parse_optional_integer(raw_row.get("cohort"), min_value=0)
        overall_value = parse_optional_measure(raw_row.get("overall"))
        education_value = parse_optional_measure(raw_row.get("education"))
        apprenticeship_value = parse_optional_measure(raw_row.get("appren"))
        employment_value = parse_optional_measure(raw_row.get("all_work"))
        not_sustained_value = parse_optional_measure(raw_row.get("all_notsust"))
        activity_unknown_value = parse_optional_measure(raw_row.get("all_unknown"))
        fe_value = parse_optional_measure(raw_row.get("fe"))
        other_education_value = parse_optional_measure(raw_row.get("other_edu"))
        school_sixth_form_value = (
            parse_optional_measure(raw_row.get("ssf")) if destination_stage == "ks4" else None
        )
        sixth_form_college_value = (
            parse_optional_measure(raw_row.get("sfc")) if destination_stage == "ks4" else None
        )
        higher_education_value = (
            parse_optional_measure(raw_row.get("he")) if destination_stage == "16_to_18" else None
        )
    except ValueError as exc:
        return None, str(exc)

    qualification_group = None
    qualification_level = None
    if destination_stage == "16_to_18":
        qualification_group = parse_optional_text(raw_row.get("cohort_level_group"))
        qualification_level = parse_optional_text(raw_row.get("cohort_level"))

    return (
        NormalizedLeaverDestinationsRow(
            academic_year=academic_year,
            destination_stage=destination_stage,
            school_urn=school_urn,
            school_laestab=school_laestab,
            school_name=school_name,
            admission_policy=parse_optional_text(raw_row.get("admission_policy")),
            entry_gender=parse_optional_text(raw_row.get("entry_gender")),
            institution_group=parse_optional_text(raw_row.get("institution_group")),
            institution_type=parse_optional_text(raw_row.get("institution_type")),
            qualification_group=qualification_group,
            qualification_level=qualification_level,
            breakdown_topic=breakdown_topic,
            breakdown=breakdown,
            data_type=data_type,
            cohort_count=cohort_count,
            overall_value=overall_value,
            education_value=education_value,
            apprenticeship_value=apprenticeship_value,
            employment_value=employment_value,
            not_sustained_value=not_sustained_value,
            activity_unknown_value=activity_unknown_value,
            fe_value=fe_value,
            other_education_value=other_education_value,
            school_sixth_form_value=school_sixth_form_value,
            sixth_form_college_value=sixth_form_college_value,
            higher_education_value=higher_education_value,
            source_file_url=source_file_url,
        ),
        None,
    )


def parse_academic_year(raw_value: str | None) -> str:
    value = parse_optional_text(raw_value)
    if value is None or len(value) != 6 or not value.isdigit():
        raise ValueError("invalid_academic_year")
    return f"{value[:4]}/{value[4:]}"


def parse_data_type(raw_value: object) -> DestinationDataType:
    value = parse_optional_text(raw_value)
    if value == "Number of students":
        return "Number of students"
    if value == "Percentage":
        return "Percentage"
    raise ValueError("invalid_data_type")


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


def parse_optional_measure(raw_value: object) -> float | None:
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
    return token


def parse_optional_text(raw_value: object) -> str | None:
    if raw_value is None:
        return None
    token = str(raw_value).strip()
    return token or None
