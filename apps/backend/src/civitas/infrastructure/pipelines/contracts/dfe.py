from __future__ import annotations

import math
from typing import Mapping, TypedDict

CONTRACT_VERSION = "dfe_characteristics.v1"

REQUIRED_HEADERS: tuple[str, ...] = (
    "school_urn",
    "time_period",
    "ptfsm6cla1a",
    "psenelek",
    "psenelk",
    "psenele",
    "ptealgrp2",
    "ptealgrp1",
    "ptealgrp3",
)

SENTINEL_TOKENS: set[str] = {"", "SUPP", "NE", "N/A", "NA", "X", "Z", "C"}


class NormalizedDfeRow(TypedDict):
    urn: str
    academic_year: str
    disadvantaged_pct: float | None
    sen_pct: float | None
    sen_support_pct: float | None
    ehcp_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None
    total_pupils: int | None
    source_dataset_id: str
    source_dataset_version: str | None


def validate_headers(headers: tuple[str, ...] | list[str]) -> None:
    header_set = set(headers)
    missing = [header for header in REQUIRED_HEADERS if header not in header_set]
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(f"DfE schema mismatch; missing required headers: {missing_fields}")


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    source_dataset_id: str,
    source_dataset_version: str | None = None,
) -> tuple[NormalizedDfeRow | None, str | None]:
    urn = raw_row["school_urn"].strip()
    if not urn:
        return None, "missing_urn"

    try:
        academic_year = normalize_academic_year(raw_row["time_period"])
    except ValueError:
        return None, "invalid_academic_year"

    try:
        disadvantaged_pct = parse_optional_percentage(raw_row["ptfsm6cla1a"])
    except ValueError:
        return None, "invalid_disadvantaged_pct"

    try:
        sen_pct = parse_optional_percentage(raw_row["psenelek"])
    except ValueError:
        return None, "invalid_sen_pct"

    try:
        sen_support_pct = parse_optional_percentage(raw_row["psenelk"])
    except ValueError:
        return None, "invalid_sen_support_pct"

    try:
        ehcp_pct = parse_optional_percentage(raw_row["psenele"])
    except ValueError:
        return None, "invalid_ehcp_pct"

    try:
        eal_pct = parse_optional_percentage(raw_row["ptealgrp2"])
    except ValueError:
        return None, "invalid_eal_pct"

    try:
        first_language_english_pct = parse_optional_percentage(raw_row["ptealgrp1"])
    except ValueError:
        return None, "invalid_first_language_english_pct"

    try:
        first_language_unclassified_pct = parse_optional_percentage(raw_row["ptealgrp3"])
    except ValueError:
        return None, "invalid_first_language_unclassified_pct"

    try:
        total_pupils = parse_total_pupils(raw_row)
    except ValueError:
        return None, "invalid_total_pupils"

    return (
        NormalizedDfeRow(
            urn=urn,
            academic_year=academic_year,
            disadvantaged_pct=disadvantaged_pct,
            sen_pct=sen_pct,
            sen_support_pct=sen_support_pct,
            ehcp_pct=ehcp_pct,
            eal_pct=eal_pct,
            first_language_english_pct=first_language_english_pct,
            first_language_unclassified_pct=first_language_unclassified_pct,
            total_pupils=total_pupils,
            source_dataset_id=source_dataset_id,
            source_dataset_version=source_dataset_version,
        ),
        None,
    )


def normalize_academic_year(raw_value: str | None) -> str:
    value = (raw_value or "").strip()

    if len(value) == 7 and value[4] == "/" and value[:4].isdigit() and value[5:].isdigit():
        return value

    # Compact format used by some source variants, e.g. 202425.
    if len(value) == 6 and value.isdigit():
        return f"{value[:4]}/{value[4:]}"

    raise ValueError("invalid academic year")


def parse_optional_percentage(raw_value: str | None) -> float | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    if value.upper() in SENTINEL_TOKENS:
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


def parse_total_pupils(raw_row: Mapping[str, str]) -> int | None:
    for field_name in ("total_pupils", "number_of_pupils"):
        raw_value = raw_row.get(field_name)
        if raw_value is None:
            continue
        value = raw_value.strip()
        if not value:
            return None
        if value.upper() in SENTINEL_TOKENS:
            return None
        try:
            return int(float(value))
        except ValueError as exc:
            raise ValueError("invalid_total_pupils") from exc
    return None
