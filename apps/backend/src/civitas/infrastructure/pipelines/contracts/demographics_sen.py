from __future__ import annotations

import math
import re
from typing import Mapping, Sequence, TypedDict

CONTRACT_VERSION = "demographics_sen.v1"

_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "urn": ("URN", "urn"),
    "time_period": ("time_period", "Time period"),
    "total_pupils": ("Total pupils",),
    "sen_support": ("SEN support",),
    "ehcp": ("EHC plan",),
}

_SENTINEL_TOKENS: set[str] = {"", "SUPP", "NE", "N/A", "NA", "X", "Z", "C"}
_PRIMARY_NEED_COUNT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^number of pupils with (?P<label>.+) as primary need$"),
    re.compile(r"^number of pupils with primary need[: ]+(?P<label>.+)$"),
)
_PRIMARY_NEED_PCT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^% of pupils with (?P<label>.+) as primary need$"),
    re.compile(r"^percentage of pupils with primary need[: ]+(?P<label>.+)$"),
)
_PRIMARY_NEED_CODE_PATTERN = re.compile(r"^(?P<prefix>ehc|sen)_primary_need_(?P<code>[a-z0-9]+)$")
_PRIMARY_NEED_CODE_LABELS: dict[str, str] = {
    "spld": "Specific learning difficulty",
    "mld": "Moderate learning difficulty",
    "sld": "Severe learning difficulty",
    "pmld": "Profound and multiple learning difficulty",
    "semh": "Social, emotional and mental health",
    "slcn": "Speech, language and communication needs",
    "hi": "Hearing impairment",
    "vi": "Visual impairment",
    "msi": "Multi-sensory impairment",
    "pd": "Physical disability",
    "asd": "Autistic spectrum disorder",
    "oth": "Other difficulty/disability",
    "nsa": "No specialist assessment",
}


class NormalizedPrimaryNeed(TypedDict):
    key: str
    label: str
    count: int | None
    percentage: float | None


class NormalizedSenRow(TypedDict):
    urn: str
    academic_year: str
    total_pupils: int | None
    sen_support_pct: float | None
    ehcp_pct: float | None
    primary_needs: tuple[NormalizedPrimaryNeed, ...]
    has_primary_need_data: bool


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
        raise ValueError("SEN schema mismatch; missing required headers: " + ", ".join(missing))

    return resolved_fields


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    column_map: Mapping[str, str],
) -> tuple[NormalizedSenRow | None, str | None]:
    urn_column = column_map["urn"]
    urn = (raw_row.get(urn_column) or "").strip()
    if not urn:
        return None, "missing_urn"

    try:
        academic_year = normalize_academic_year(raw_row.get(column_map["time_period"]))
    except ValueError:
        return None, "invalid_academic_year"

    try:
        total_pupils = _parse_optional_int(raw_row.get(column_map["total_pupils"]))
    except ValueError:
        return None, "invalid_total_pupils"

    try:
        sen_support = _parse_optional_float(raw_row.get(column_map["sen_support"]))
    except ValueError:
        return None, "invalid_sen_support"

    try:
        ehcp = _parse_optional_float(raw_row.get(column_map["ehcp"]))
    except ValueError:
        return None, "invalid_ehcp"

    if total_pupils is None or total_pupils <= 0:
        sen_support_pct = None
        ehcp_pct = None
    else:
        try:
            sen_support_pct = _to_percentage(sen_support, total_pupils)
        except ValueError:
            return None, "invalid_sen_support"
        try:
            ehcp_pct = _to_percentage(ehcp, total_pupils)
        except ValueError:
            return None, "invalid_ehcp"

    primary_needs = _extract_primary_needs(raw_row)
    primary_needs = _derive_primary_need_percentages(
        primary_needs=primary_needs,
        total_pupils=total_pupils,
    )

    return (
        NormalizedSenRow(
            urn=urn,
            academic_year=academic_year,
            total_pupils=total_pupils,
            sen_support_pct=sen_support_pct,
            ehcp_pct=ehcp_pct,
            primary_needs=primary_needs,
            has_primary_need_data=len(primary_needs) > 0,
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


def _parse_optional_int(raw_value: str | None) -> int | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value or value.upper() in _SENTINEL_TOKENS:
        return None

    try:
        parsed = int(float(value))
    except ValueError as exc:
        raise ValueError("invalid integer") from exc

    if parsed < 0:
        raise ValueError("invalid integer")

    return parsed


def _parse_optional_float(raw_value: str | None) -> float | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value or value.upper() in _SENTINEL_TOKENS:
        return None

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError("invalid float") from exc

    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError("invalid float")

    return parsed


def _to_percentage(value: float | None, total: int) -> float | None:
    if value is None:
        return None
    percentage = (value / total) * 100.0
    if percentage < 0.0 or percentage > 100.0:
        raise ValueError("percentage out of range")
    return percentage


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


def _extract_primary_needs(raw_row: Mapping[str, str]) -> tuple[NormalizedPrimaryNeed, ...]:
    by_key: dict[str, NormalizedPrimaryNeed] = {}

    for header, raw_value in raw_row.items():
        normalized_header = _normalize_header(header)

        count_label = _match_primary_need_label(
            normalized_header, patterns=_PRIMARY_NEED_COUNT_PATTERNS
        )
        if count_label is not None:
            key = _primary_need_key(count_label)
            entry = by_key.setdefault(
                key,
                NormalizedPrimaryNeed(
                    key=key,
                    label=_display_primary_need_label(count_label),
                    count=None,
                    percentage=None,
                ),
            )
            try:
                entry["count"] = _parse_optional_int(raw_value)
            except ValueError:
                entry["count"] = None
            continue

        pct_label = _match_primary_need_label(
            normalized_header, patterns=_PRIMARY_NEED_PCT_PATTERNS
        )
        if pct_label is None:
            coded_need = _extract_coded_primary_need(normalized_header)
            if coded_need is None:
                continue
            key, label = coded_need
            entry = by_key.setdefault(
                key,
                NormalizedPrimaryNeed(
                    key=key,
                    label=label,
                    count=None,
                    percentage=None,
                ),
            )
            try:
                entry["count"] = _parse_optional_int(raw_value)
            except ValueError:
                entry["count"] = None
            continue

        key = _primary_need_key(pct_label)
        entry = by_key.setdefault(
            key,
            NormalizedPrimaryNeed(
                key=key,
                label=_display_primary_need_label(pct_label),
                count=None,
                percentage=None,
            ),
        )
        try:
            entry["percentage"] = _parse_optional_float(raw_value)
        except ValueError:
            entry["percentage"] = None

    ranked = sorted(
        by_key.values(),
        key=lambda item: (
            item["count"] is None,
            -(item["count"] or 0),
            item["percentage"] is None,
            -(item["percentage"] or 0.0),
            item["label"],
        ),
    )
    return tuple(ranked)


def _match_primary_need_label(
    normalized_header: str,
    *,
    patterns: Sequence[re.Pattern[str]],
) -> str | None:
    for pattern in patterns:
        match = pattern.match(normalized_header)
        if match is None:
            continue
        label = match.group("label").strip()
        if label:
            return label
    return None


def _primary_need_key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")


def _display_primary_need_label(label: str) -> str:
    return " ".join(segment.capitalize() for segment in label.split())


def _extract_coded_primary_need(normalized_header: str) -> tuple[str, str] | None:
    match = _PRIMARY_NEED_CODE_PATTERN.match(normalized_header)
    if match is None:
        return None

    need_code = match.group("code").strip().casefold()
    if not need_code:
        return None

    label = _PRIMARY_NEED_CODE_LABELS.get(need_code)
    if label is None:
        return None

    key = _primary_need_key(label)
    return key, label


def _derive_primary_need_percentages(
    *,
    primary_needs: tuple[NormalizedPrimaryNeed, ...],
    total_pupils: int | None,
) -> tuple[NormalizedPrimaryNeed, ...]:
    if total_pupils is None or total_pupils <= 0:
        return primary_needs

    derived: list[NormalizedPrimaryNeed] = []
    for need in primary_needs:
        percentage = need["percentage"]
        count = need["count"]
        if percentage is None and count is not None:
            percentage = _to_percentage(float(count), total_pupils)
        derived.append(
            NormalizedPrimaryNeed(
                key=need["key"],
                label=need["label"],
                count=count,
                percentage=percentage,
            )
        )

    return tuple(derived)
