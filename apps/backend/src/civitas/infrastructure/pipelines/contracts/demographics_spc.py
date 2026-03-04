from __future__ import annotations

import math
import re
from typing import Mapping, Sequence, TypedDict

CONTRACT_VERSION = "demographics_spc.v1"

_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "urn": ("urn", "URN"),
    "fsm_pct": ("% of pupils known to be eligible for free school meals",),
    "disadvantaged_pct": (
        "% of pupils known to be eligible for free school meals (Performance Tables)",
    ),
    "eal_pct": ("% of pupils whose first language is known or believed to be other than English",),
    "first_language_english_pct": (
        "% of pupils whose first language is known or believed to be English",
    ),
    "first_language_unclassified_pct": ("% of pupils whose first language is unclassified",),
}

_TIME_PERIOD_FIELDS: tuple[str, ...] = ("time_period", "Time period")
_SENTINEL_TOKENS: set[str] = {"", "SUPP", "NE", "N/A", "NA", "X", "Z", "C"}
_RELEASE_SLUG_PATTERN = re.compile(r"^(?P<start>\d{4})-(?P<end>\d{2})$")


class NormalizedSpcRow(TypedDict):
    urn: str
    academic_year: str
    fsm_pct: float | None
    disadvantaged_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None


def validate_headers(headers: Sequence[str]) -> dict[str, str]:
    normalized_headers = {_normalize_header(header): header for header in headers}

    resolved_fields: dict[str, str] = {}
    missing: list[str] = []

    for field_name, candidates in _REQUIRED_FIELDS.items():
        resolved = _resolve_candidate(candidates, normalized_headers)
        if resolved is None:
            missing.append(candidates[0])
            continue
        resolved_fields[field_name] = resolved

    if missing:
        raise ValueError("SPC schema mismatch; missing required headers: " + ", ".join(missing))

    time_period_column = _resolve_candidate(_TIME_PERIOD_FIELDS, normalized_headers)
    if time_period_column is not None:
        resolved_fields["time_period"] = time_period_column

    return resolved_fields


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    column_map: Mapping[str, str],
    release_slug: str,
) -> tuple[NormalizedSpcRow | None, str | None]:
    urn_column = column_map["urn"]
    urn = (raw_row.get(urn_column) or "").strip()
    if not urn:
        return None, "missing_urn"

    try:
        academic_year = _resolve_academic_year(
            raw_row=raw_row, column_map=column_map, release_slug=release_slug
        )
    except ValueError:
        return None, "invalid_academic_year"

    try:
        fsm_pct = _parse_optional_percentage(raw_row.get(column_map["fsm_pct"]))
    except ValueError:
        return None, "invalid_fsm_pct"

    try:
        disadvantaged_pct = _parse_optional_percentage(raw_row.get(column_map["disadvantaged_pct"]))
    except ValueError:
        return None, "invalid_disadvantaged_pct"

    try:
        eal_pct = _parse_optional_percentage(raw_row.get(column_map["eal_pct"]))
    except ValueError:
        return None, "invalid_eal_pct"

    try:
        first_language_english_pct = _parse_optional_percentage(
            raw_row.get(column_map["first_language_english_pct"])
        )
    except ValueError:
        return None, "invalid_first_language_english_pct"

    try:
        first_language_unclassified_pct = _parse_optional_percentage(
            raw_row.get(column_map["first_language_unclassified_pct"])
        )
    except ValueError:
        return None, "invalid_first_language_unclassified_pct"

    return (
        NormalizedSpcRow(
            urn=urn,
            academic_year=academic_year,
            fsm_pct=fsm_pct,
            disadvantaged_pct=disadvantaged_pct,
            eal_pct=eal_pct,
            first_language_english_pct=first_language_english_pct,
            first_language_unclassified_pct=first_language_unclassified_pct,
        ),
        None,
    )


def normalize_academic_year(raw_value: str | None) -> str:
    value = (raw_value or "").strip()

    if len(value) == 7 and value[4] == "/" and value[:4].isdigit() and value[5:].isdigit():
        return value

    if len(value) == 6 and value.isdigit():
        return f"{value[:4]}/{value[4:]}"

    raise ValueError("invalid academic year")


def parse_release_slug_academic_year(release_slug: str) -> str:
    match = _RELEASE_SLUG_PATTERN.match(release_slug.strip())
    if match is None:
        raise ValueError("invalid release slug")

    start_year = int(match.group("start"))
    end_suffix = int(match.group("end"))
    if start_year % 100 != ((end_suffix - 1) % 100):
        raise ValueError("invalid release slug")

    return f"{start_year:04d}/{end_suffix:02d}"


def _resolve_academic_year(
    *,
    raw_row: Mapping[str, str],
    column_map: Mapping[str, str],
    release_slug: str,
) -> str:
    time_period_column = column_map.get("time_period")
    if time_period_column is not None:
        raw_time_period = raw_row.get(time_period_column)
        if raw_time_period is not None and raw_time_period.strip():
            return normalize_academic_year(raw_time_period)
    return parse_release_slug_academic_year(release_slug)


def _parse_optional_percentage(raw_value: str | None) -> float | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    if value.upper() in _SENTINEL_TOKENS:
        return None

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError("invalid numeric value") from exc

    if not math.isfinite(parsed):
        raise ValueError("numeric value must be finite")
    if parsed < 0.0 or parsed > 100.0:
        raise ValueError("percentage out of range")

    return parsed


def _resolve_candidate(
    candidates: Sequence[str],
    normalized_headers: Mapping[str, str],
) -> str | None:
    for candidate in candidates:
        resolved = normalized_headers.get(_normalize_header(candidate))
        if resolved is not None:
            return resolved
    return None


def _normalize_header(value: str) -> str:
    return value.lstrip("\ufeff").strip().casefold()
