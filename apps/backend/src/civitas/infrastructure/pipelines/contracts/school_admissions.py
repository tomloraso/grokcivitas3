from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TypedDict

CONTRACT_VERSION = "school_admissions.v1"

NULL_TOKENS: set[str] = {
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
    "la_name",
    "school_phase",
    "school_laestab_as_used",
    "school_name",
    "total_number_places_offered",
    "number_preferred_offers",
    "number_1st_preference_offers",
    "number_2nd_preference_offers",
    "number_3rd_preference_offers",
    "times_put_as_any_preferred_school",
    "times_put_as_1st_preference",
    "times_put_as_2nd_preference",
    "times_put_as_3rd_preference",
    "proportion_1stprefs_v_1stprefoffers",
    "proportion_1stprefs_v_totaloffers",
    "all_applications_from_another_LA",
    "offers_to_applicants_from_another_LA",
    "establishment_type",
    "denomination",
    "FSM_eligible_percent",
    "admissions_policy",
    "urban_rural",
    "allthrough_school",
    "school_urn",
    "entry_year",
)


class NormalizedSchoolAdmissionsRow(TypedDict):
    academic_year: str
    entry_year: str | None
    school_urn: str | None
    school_laestab: str | None
    school_phase: str | None
    school_name: str
    places_offered_total: int | None
    preferred_offers_total: int | None
    first_preference_offers: int | None
    second_preference_offers: int | None
    third_preference_offers: int | None
    applications_any_preference: int | None
    applications_first_preference: int | None
    applications_second_preference: int | None
    applications_third_preference: int | None
    first_preference_application_to_offer_ratio: float | None
    first_preference_application_to_total_places_ratio: float | None
    cross_la_applications: int | None
    cross_la_offers: int | None
    admissions_policy: str | None
    establishment_type: str | None
    denomination: str | None
    fsm_eligible_pct: float | None
    urban_rural: str | None
    allthrough_school: bool | None
    source_file_url: str


def validate_headers(headers: list[str] | tuple[str, ...]) -> None:
    header_set = set(headers)
    missing = [header for header in REQUIRED_HEADERS if header not in header_set]
    if missing:
        raise ValueError(
            "School admissions schema mismatch; missing required headers: " + ", ".join(missing)
        )


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    source_file_url: str,
) -> tuple[NormalizedSchoolAdmissionsRow | None, str | None]:
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

    school_name = parse_optional_text(raw_row.get("school_name"))
    if school_name is None:
        return None, "missing_school_name"

    school_urn = parse_optional_text(raw_row.get("school_urn"))
    if school_urn is not None and (len(school_urn) != 6 or not school_urn.isdigit()):
        return None, "invalid_school_urn"

    school_laestab = parse_optional_text(raw_row.get("school_laestab_as_used"))
    if school_laestab is not None and not school_laestab.isdigit():
        return None, "invalid_school_laestab"

    if school_urn is None and school_laestab is None:
        return None, "missing_school_identifier"

    try:
        places_offered_total = parse_optional_integer(
            raw_row.get("total_number_places_offered"),
            min_value=0,
        )
        preferred_offers_total = parse_optional_integer(
            raw_row.get("number_preferred_offers"),
            min_value=0,
        )
        first_preference_offers = parse_optional_integer(
            raw_row.get("number_1st_preference_offers"),
            min_value=0,
        )
        second_preference_offers = parse_optional_integer(
            raw_row.get("number_2nd_preference_offers"),
            min_value=0,
        )
        third_preference_offers = parse_optional_integer(
            raw_row.get("number_3rd_preference_offers"),
            min_value=0,
        )
        applications_any_preference = parse_optional_integer(
            raw_row.get("times_put_as_any_preferred_school"),
            min_value=0,
        )
        applications_first_preference = parse_optional_integer(
            raw_row.get("times_put_as_1st_preference"),
            min_value=0,
        )
        applications_second_preference = parse_optional_integer(
            raw_row.get("times_put_as_2nd_preference"),
            min_value=0,
        )
        applications_third_preference = parse_optional_integer(
            raw_row.get("times_put_as_3rd_preference"),
            min_value=0,
        )
        first_preference_application_to_offer_ratio = parse_optional_float(
            raw_row.get("proportion_1stprefs_v_1stprefoffers"),
            min_value=0.0,
        )
        first_preference_application_to_total_places_ratio = parse_optional_float(
            raw_row.get("proportion_1stprefs_v_totaloffers"),
            min_value=0.0,
        )
        cross_la_applications = parse_optional_integer(
            raw_row.get("all_applications_from_another_LA"),
            min_value=0,
        )
        cross_la_offers = parse_optional_integer(
            raw_row.get("offers_to_applicants_from_another_LA"),
            min_value=0,
        )
        fsm_eligible_pct = parse_optional_float(
            raw_row.get("FSM_eligible_percent"),
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError as exc:
        return None, str(exc)

    try:
        allthrough_school = parse_optional_boolean(raw_row.get("allthrough_school"))
    except ValueError:
        return None, "invalid_allthrough_school"

    return (
        NormalizedSchoolAdmissionsRow(
            academic_year=academic_year,
            entry_year=parse_optional_text(raw_row.get("entry_year")),
            school_urn=school_urn,
            school_laestab=school_laestab,
            school_phase=parse_optional_text(raw_row.get("school_phase")),
            school_name=school_name,
            places_offered_total=places_offered_total,
            preferred_offers_total=preferred_offers_total,
            first_preference_offers=first_preference_offers,
            second_preference_offers=second_preference_offers,
            third_preference_offers=third_preference_offers,
            applications_any_preference=applications_any_preference,
            applications_first_preference=applications_first_preference,
            applications_second_preference=applications_second_preference,
            applications_third_preference=applications_third_preference,
            first_preference_application_to_offer_ratio=(
                first_preference_application_to_offer_ratio
            ),
            first_preference_application_to_total_places_ratio=(
                first_preference_application_to_total_places_ratio
            ),
            cross_la_applications=cross_la_applications,
            cross_la_offers=cross_la_offers,
            admissions_policy=parse_optional_text(raw_row.get("admissions_policy")),
            establishment_type=parse_optional_text(raw_row.get("establishment_type")),
            denomination=parse_optional_text(raw_row.get("denomination")),
            fsm_eligible_pct=fsm_eligible_pct,
            urban_rural=parse_optional_text(raw_row.get("urban_rural")),
            allthrough_school=allthrough_school,
            source_file_url=source_file_url,
        ),
        None,
    )


def parse_academic_year(raw_value: str | None) -> str:
    value = parse_optional_text(raw_value)
    if value is None or len(value) != 6 or not value.isdigit():
        raise ValueError("invalid_academic_year")
    start_year = value[:4]
    end_year = value[4:]
    return f"{start_year}/{end_year}"


def parse_optional_integer(
    value: object,
    *,
    min_value: int | None = None,
) -> int | None:
    normalized = parse_optional_text(value)
    if normalized is None:
        return None
    try:
        parsed = int(normalized)
    except ValueError as exc:
        raise ValueError("invalid_integer") from exc
    if min_value is not None and parsed < min_value:
        raise ValueError("invalid_integer")
    return parsed


def parse_optional_float(
    value: object,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float | None:
    normalized = parse_optional_text(value)
    if normalized is None:
        return None
    try:
        parsed = float(normalized)
    except ValueError as exc:
        raise ValueError("invalid_float") from exc
    if not math.isfinite(parsed):
        raise ValueError("invalid_float")
    if min_value is not None and parsed < min_value:
        raise ValueError("invalid_float")
    if max_value is not None and parsed > max_value:
        raise ValueError("invalid_float")
    return parsed


def parse_optional_boolean(value: object) -> bool | None:
    normalized = parse_optional_text(value)
    if normalized is None:
        return None
    token = normalized.casefold()
    if token == "yes":
        return True
    if token == "no":
        return False
    raise ValueError("invalid_allthrough_school")


def parse_optional_text(value: object) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    if token.casefold() in NULL_TOKENS:
        return None
    return token
