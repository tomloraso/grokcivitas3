from __future__ import annotations

import math

CONTRACT_VERSION = "dfe_performance.v1"

KS4_INDICATOR_IDS: dict[str, str] = {
    "attainment8_average": "kgVhs",
    "progress8_average": "Pwoeb",
    "engmath_5_plus_pct": "dDo0Z",
    "engmath_4_plus_pct": "hCRyW",
    "ebacc_entry_pct": "bmztT",
    "ebacc_5_plus_pct": "uEko4",
    "ebacc_4_plus_pct": "mqo9K",
}

KS4_FILTER_IDS: dict[str, str] = {
    "disadvantage_status": "pPmSo",
    "first_language": "IzpBz",
    "mobility_status": "ibG6X",
    "sex": "LZ6Wj",
}

KS4_FILTER_OPTION_IDS: dict[str, str] = {
    "disadvantage_total": "5Kydi",
    "disadvantage_disadvantaged": "D5IQe",
    "disadvantage_not_disadvantaged": "eN2uS",
    "first_language_total": "mws9K",
    "mobility_total": "WCb2b",
    "sex_total": "9b64v",
}

KS2_INDICATOR_IDS: dict[str, str] = {
    "expected_standard_pct": "IwjBz",
    "higher_standard_pct": "i2s6X",
}

KS2_FILTER_IDS: dict[str, str] = {
    "breakdown": "fV8YF",
    "subject": "jfhAM",
}

KS2_FILTER_OPTION_IDS: dict[str, str] = {
    "breakdown_total": "EXcPq",
    "subject_reading": "2id7l",
    "subject_writing": "wIWob",
    "subject_maths": "9lHt4",
    "subject_combined": "PyBQe",
}

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


def normalize_academic_year(value: str) -> str:
    raw = value.strip()
    if len(raw) == 7 and raw[4] == "/" and raw[:4].isdigit() and raw[5:].isdigit():
        return f"{raw[:4]}/{raw[5:]}"
    if len(raw) == 9 and raw[4] == "/" and raw[:4].isdigit() and raw[5:].isdigit():
        return f"{raw[:4]}/{raw[7:]}"
    raise ValueError("invalid academic year")


def normalize_academic_year_from_period(value: str) -> str:
    return normalize_academic_year(value)


def to_api_academic_year_period(academic_year: str) -> str:
    normalized = normalize_academic_year(academic_year)
    start_year = int(normalized[:4])
    end_year = start_year + 1
    return f"{start_year:04d}/{end_year:04d}"


def expand_academic_years(
    *,
    start_period: str | None,
    end_period: str | None,
    lookback_years: int,
) -> tuple[str, ...]:
    if lookback_years <= 0:
        return ()
    if start_period is None or end_period is None:
        return ()

    start_year = _academic_year_start(normalize_academic_year(start_period))
    end_year = _academic_year_start(normalize_academic_year(end_period))
    if end_year < start_year:
        return ()

    selected_start_year = max(start_year, end_year - lookback_years + 1)
    return tuple(
        f"{year:04d}/{(year + 1) % 100:02d}" for year in range(selected_start_year, end_year + 1)
    )


def parse_optional_number(value: object) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("numeric value must be finite")
        return parsed

    if not isinstance(value, str):
        raise ValueError("numeric value must be string-compatible")

    token = value.strip()
    if token.casefold() in NULL_TOKENS:
        return None

    try:
        parsed = float(token)
    except ValueError as exc:
        raise ValueError("invalid numeric value") from exc

    if not math.isfinite(parsed):
        raise ValueError("numeric value must be finite")
    return parsed


def _academic_year_start(value: str) -> int:
    normalized = normalize_academic_year(value)
    return int(normalized[:4])
