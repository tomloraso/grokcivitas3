from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date, datetime
from typing import TypedDict

CONTRACT_VERSION = "dfe_workforce.v1"

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


class NormalizedWorkforceRow(TypedDict):
    urn: str
    academic_year: str
    pupil_teacher_ratio: float | None
    supply_staff_pct: float | None
    teachers_3plus_years_pct: float | None
    teacher_turnover_pct: float | None
    qts_pct: float | None
    qualifications_level6_plus_pct: float | None
    headteacher_name: str | None
    headteacher_start_date: date | None
    headteacher_tenure_years: float | None
    leadership_turnover_score: float | None
    source_dataset_id: str
    source_dataset_version: str | None


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    release_slug: str,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedWorkforceRow | None, str | None]:
    urn_raw = (_pick(raw_row, "school_urn", "urn", "URN") or "").strip()
    if len(urn_raw) != 6 or not urn_raw.isdigit():
        return None, "invalid_urn"

    academic_year_raw = (_pick(raw_row, "time_period", "academic_year") or "").strip()
    if not academic_year_raw:
        academic_year_raw = release_slug.replace("-", "")
    try:
        academic_year = normalize_academic_year(academic_year_raw)
    except ValueError:
        return None, "invalid_academic_year"

    try:
        pupil_teacher_ratio = parse_optional_numeric(
            _pick(
                raw_row,
                "pupil_teacher_ratio",
                "ptr",
                "pupil_to_qual_unqual_teacher_ratio",
                "pupil_to_qual_teacher_ratio",
            ),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_pupil_teacher_ratio"

    supply_source = _pick(raw_row, "supply_teacher_pct", "supply_staff_pct")
    if supply_source is None:
        try:
            supply_staff_pct = _derive_optional_percentage_from_counts(
                numerator_raw=_pick(raw_row, "hc_occasional_teachers"),
                denominator_raw=_pick(raw_row, "hc_all_teachers"),
            )
        except ValueError:
            return None, "invalid_supply_staff_pct"
    else:
        try:
            supply_staff_pct = parse_optional_numeric(
                supply_source,
                min_value=0.0,
                max_value=100.0,
            )
        except ValueError:
            return None, "invalid_supply_staff_pct"

    try:
        teachers_3plus_years_pct = parse_optional_numeric(
            _pick(raw_row, "teachers_3plus_years_pct", "experienced_teachers_pct"),
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError:
        return None, "invalid_teachers_3plus_years_pct"

    try:
        teacher_turnover_pct = parse_optional_numeric(
            _pick(raw_row, "teacher_turnover_pct"),
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError:
        return None, "invalid_teacher_turnover_pct"

    qts_source = _pick(raw_row, "qts_pct")
    if qts_source is None:
        try:
            qts_pct = _derive_qts_percentage_from_counts(
                total_teachers_raw=_pick(raw_row, "hc_all_teachers"),
                unqualified_teachers_raw=_pick(raw_row, "hc_all_teachers_without_qts"),
            )
        except ValueError:
            return None, "invalid_qts_pct"
    else:
        try:
            qts_pct = parse_optional_numeric(
                qts_source,
                min_value=0.0,
                max_value=100.0,
            )
        except ValueError:
            return None, "invalid_qts_pct"

    try:
        qualifications_level6_plus_pct = parse_optional_numeric(
            _pick(
                raw_row,
                "qualifications_level6_plus_pct",
                "teachers_with_level6_plus_qualification_pct",
            ),
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError:
        return None, "invalid_qualifications_level6_plus_pct"

    try:
        headteacher_start_date = parse_optional_date(
            _pick(raw_row, "headteacher_start_date", "head_start_date")
        )
    except ValueError:
        return None, "invalid_headteacher_start_date"

    try:
        headteacher_tenure_years = parse_optional_numeric(
            _pick(raw_row, "headteacher_tenure_years"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_headteacher_tenure_years"

    try:
        leadership_turnover_score = parse_optional_numeric(
            _pick(raw_row, "leadership_turnover_score"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_leadership_turnover_score"

    return (
        NormalizedWorkforceRow(
            urn=urn_raw,
            academic_year=academic_year,
            pupil_teacher_ratio=pupil_teacher_ratio,
            supply_staff_pct=supply_staff_pct,
            teachers_3plus_years_pct=teachers_3plus_years_pct,
            teacher_turnover_pct=teacher_turnover_pct,
            qts_pct=qts_pct,
            qualifications_level6_plus_pct=qualifications_level6_plus_pct,
            headteacher_name=parse_optional_text(_pick(raw_row, "headteacher_name", "head_name")),
            headteacher_start_date=headteacher_start_date,
            headteacher_tenure_years=headteacher_tenure_years,
            leadership_turnover_score=leadership_turnover_score,
            source_dataset_id=f"workforce:{release_version_id}",
            source_dataset_version=f"workforce:{file_id}",
        ),
        None,
    )


def normalize_academic_year(value: str) -> str:
    raw = value.strip()
    if len(raw) == 4 and raw.isdigit():
        start_year = int(raw)
        return f"{start_year:04d}/{(start_year + 1) % 100:02d}"
    if len(raw) == 6 and raw.isdigit():
        return f"{raw[:4]}/{raw[4:]}"
    if len(raw) == 7 and raw[4] == "/" and raw[:4].isdigit() and raw[5:].isdigit():
        return f"{raw[:4]}/{raw[5:]}"
    if len(raw) == 9 and raw[4] == "/" and raw[:4].isdigit() and raw[5:].isdigit():
        return f"{raw[:4]}/{raw[7:]}"
    raise ValueError("invalid academic year")


def parse_optional_numeric(
    value: object,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        parsed = float(value)
    elif isinstance(value, str):
        token = value.strip().replace(",", "")
        if token.casefold() in NULL_TOKENS:
            return None
        if token.endswith("%"):
            token = token[:-1].strip()
        try:
            parsed = float(token)
        except ValueError as exc:
            raise ValueError("invalid numeric value") from exc
    else:
        raise ValueError("unsupported numeric value type")

    if not math.isfinite(parsed):
        raise ValueError("numeric value must be finite")
    if min_value is not None and parsed < min_value:
        raise ValueError("numeric value below minimum")
    if max_value is not None and parsed > max_value:
        raise ValueError("numeric value above maximum")
    return parsed


def parse_optional_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError("unsupported date value type")

    token = value.strip()
    if token.casefold() in NULL_TOKENS:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(token, fmt).date()
        except ValueError:
            continue
    raise ValueError("invalid date format")


def parse_optional_text(value: object) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    if token.casefold() in NULL_TOKENS:
        return None
    return token


def _pick(raw_row: Mapping[str, str], *keys: str) -> str | None:
    for key in keys:
        if key in raw_row:
            return raw_row.get(key)
    return None


def _derive_optional_percentage_from_counts(
    *,
    numerator_raw: object,
    denominator_raw: object,
) -> float | None:
    numerator = parse_optional_numeric(numerator_raw, min_value=0.0)
    denominator = parse_optional_numeric(denominator_raw, min_value=0.0)
    if numerator is None or denominator is None:
        return None
    if denominator <= 0.0:
        return None
    return (numerator / denominator) * 100.0


def _derive_qts_percentage_from_counts(
    *,
    total_teachers_raw: object,
    unqualified_teachers_raw: object,
) -> float | None:
    total_teachers = parse_optional_numeric(total_teachers_raw, min_value=0.0)
    unqualified_teachers = parse_optional_numeric(unqualified_teachers_raw, min_value=0.0)
    if total_teachers is None or unqualified_teachers is None:
        return None
    if total_teachers <= 0.0:
        return None
    qualified_teachers = total_teachers - unqualified_teachers
    if qualified_teachers < 0.0:
        raise ValueError("qualified teachers below zero")
    return (qualified_teachers / total_teachers) * 100.0
