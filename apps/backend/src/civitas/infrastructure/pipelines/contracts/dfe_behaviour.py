from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TypedDict

CONTRACT_VERSION = "dfe_behaviour.v1"

NULL_TOKENS: set[str] = {
    "",
    ".",
    "supp",
    "ne",
    "n/a",
    "na",
    "x",
    "z",
    "c",
    "u",
}


class NormalizedBehaviourRow(TypedDict):
    urn: str
    academic_year: str
    suspensions_count: int | None
    suspensions_rate: float | None
    permanent_exclusions_count: int | None
    permanent_exclusions_rate: float | None
    source_dataset_id: str
    source_dataset_version: str | None


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    release_slug: str,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedBehaviourRow | None, str | None]:
    urn_raw = (raw_row.get("school_urn") or "").strip()
    if len(urn_raw) != 6 or not urn_raw.isdigit():
        return None, "invalid_urn"

    academic_year_raw = (raw_row.get("time_period") or "").strip()
    if not academic_year_raw:
        academic_year_raw = release_slug.replace("-", "")
    try:
        academic_year = normalize_academic_year(academic_year_raw)
    except ValueError:
        return None, "invalid_academic_year"

    try:
        suspensions_count = parse_optional_count(raw_row.get("suspension"))
    except ValueError:
        return None, "invalid_suspensions_count"
    try:
        suspensions_rate = parse_optional_rate(raw_row.get("susp_rate"))
    except ValueError:
        return None, "invalid_suspensions_rate"
    try:
        permanent_exclusions_count = parse_optional_count(raw_row.get("perm_excl"))
    except ValueError:
        return None, "invalid_permanent_exclusions_count"
    try:
        permanent_exclusions_rate = parse_optional_rate(raw_row.get("perm_excl_rate"))
    except ValueError:
        return None, "invalid_permanent_exclusions_rate"

    return (
        NormalizedBehaviourRow(
            urn=urn_raw,
            academic_year=academic_year,
            suspensions_count=suspensions_count,
            suspensions_rate=suspensions_rate,
            permanent_exclusions_count=permanent_exclusions_count,
            permanent_exclusions_rate=permanent_exclusions_rate,
            source_dataset_id=f"behaviour:{release_version_id}",
            source_dataset_version=f"behaviour:{file_id}",
        ),
        None,
    )


def normalize_academic_year(value: str) -> str:
    raw = value.strip()
    if len(raw) == 6 and raw.isdigit():
        return f"{raw[:4]}/{raw[4:]}"
    if len(raw) == 7 and raw[4] == "/" and raw[:4].isdigit() and raw[5:].isdigit():
        return f"{raw[:4]}/{raw[5:]}"
    if len(raw) == 9 and raw[4] == "/" and raw[:4].isdigit() and raw[5:].isdigit():
        return f"{raw[:4]}/{raw[7:]}"
    raise ValueError("invalid academic year")


def parse_optional_count(value: object) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        raise ValueError("unsupported count type")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("count out of range")
        return value
    if isinstance(value, float):
        if not math.isfinite(value) or value < 0 or not value.is_integer():
            raise ValueError("count out of range")
        return int(value)

    if not isinstance(value, str):
        raise ValueError("unsupported count type")

    token = value.strip()
    if token.casefold() in NULL_TOKENS:
        return None
    try:
        parsed = float(token)
    except ValueError as exc:
        raise ValueError("invalid count") from exc
    if not math.isfinite(parsed) or parsed < 0 or not parsed.is_integer():
        raise ValueError("count out of range")
    return int(parsed)


def parse_optional_rate(value: object) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        parsed = float(value)
    elif isinstance(value, str):
        token = value.strip()
        if token.casefold() in NULL_TOKENS:
            return None
        try:
            parsed = float(token)
        except ValueError as exc:
            raise ValueError("invalid rate") from exc
    else:
        raise ValueError("unsupported rate type")

    if not math.isfinite(parsed):
        raise ValueError("rate must be finite")
    if parsed < 0:
        raise ValueError("rate must be non-negative")
    return parsed
