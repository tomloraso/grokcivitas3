from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TypedDict

CONTRACT_VERSION = "dfe_attendance.v1"

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


class NormalizedAttendanceRow(TypedDict):
    urn: str
    academic_year: str
    overall_absence_pct: float | None
    overall_attendance_pct: float | None
    persistent_absence_pct: float | None
    source_dataset_id: str
    source_dataset_version: str | None


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    release_slug: str,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedAttendanceRow | None, str | None]:
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
        overall_absence_pct = parse_optional_percentage(
            raw_row.get("sess_overall_percent"),
            allow_over_100=False,
        )
    except ValueError:
        return None, "invalid_overall_absence_pct"

    overall_attendance_pct = (
        None if overall_absence_pct is None else max(0.0, 100.0 - overall_absence_pct)
    )

    try:
        persistent_absence_pct = parse_optional_percentage(
            raw_row.get("enrolments_pa_10_exact_percent"),
            allow_over_100=False,
        )
    except ValueError:
        return None, "invalid_persistent_absence_pct"

    return (
        NormalizedAttendanceRow(
            urn=urn_raw,
            academic_year=academic_year,
            overall_absence_pct=overall_absence_pct,
            overall_attendance_pct=overall_attendance_pct,
            persistent_absence_pct=persistent_absence_pct,
            source_dataset_id=f"attendance:{release_version_id}",
            source_dataset_version=f"attendance:{file_id}",
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


def parse_optional_percentage(value: object, *, allow_over_100: bool) -> float | None:
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
            raise ValueError("invalid numeric value") from exc
    else:
        raise ValueError("unsupported numeric value type")

    if not math.isfinite(parsed):
        raise ValueError("numeric value must be finite")
    if parsed < 0:
        raise ValueError("numeric value must be non-negative")
    if not allow_over_100 and parsed > 100:
        raise ValueError("percentage out of range")
    return parsed
