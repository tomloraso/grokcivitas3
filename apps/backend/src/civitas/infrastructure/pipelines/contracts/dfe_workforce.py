from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date, datetime
from typing import TypedDict

CONTRACT_VERSION = "dfe_workforce.v2"

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


class NormalizedLegacyWorkforceRow(TypedDict):
    urn: str
    academic_year: str
    pupil_teacher_ratio: float | None
    supply_staff_pct: float | None
    teachers_3plus_years_pct: float | None
    teacher_turnover_pct: float | None
    qts_pct: float | None
    qualifications_level6_plus_pct: float | None
    source_dataset_id: str
    source_dataset_version: str | None


class NormalizedTeacherCharacteristicsRow(TypedDict):
    urn: str
    academic_year: str
    school_laestab: str | None
    school_name: str
    school_type: str | None
    characteristic_group: str
    characteristic: str
    grade: str | None
    sex: str | None
    age_group: str | None
    working_pattern: str | None
    qts_status: str | None
    on_route: str | None
    ethnicity_major: str | None
    teacher_fte: float | None
    teacher_headcount: float | None
    teacher_fte_pct: float | None
    teacher_headcount_pct: float | None
    source_dataset_id: str
    source_dataset_version: str | None


class NormalizedSupportStaffCharacteristicsRow(TypedDict):
    urn: str
    academic_year: str
    school_laestab: str | None
    school_name: str
    school_type: str | None
    post: str
    sex: str
    ethnicity_major: str
    support_staff_fte: float | None
    support_staff_headcount: float | None
    source_dataset_id: str
    source_dataset_version: str | None


class NormalizedTeacherPayRow(TypedDict):
    urn: str
    academic_year: str
    teacher_headcount_all: float | None
    teacher_average_mean_salary_gbp: float | None
    teacher_average_median_salary_gbp: float | None
    teachers_on_leadership_pay_range_pct: float | None
    source_dataset_id: str
    source_dataset_version: str | None


class NormalizedTeacherAbsenceRow(TypedDict):
    urn: str
    academic_year: str
    teachers_taking_absence_count: float | None
    teacher_absence_pct: float | None
    teacher_absence_days_total: float | None
    teacher_absence_days_average: float | None
    teacher_absence_days_average_all_teachers: float | None
    source_dataset_id: str
    source_dataset_version: str | None


class NormalizedTeacherVacancyRow(TypedDict):
    urn: str
    academic_year: str
    teacher_vacancy_count: float | None
    teacher_vacancy_rate: float | None
    teacher_tempfilled_vacancy_count: float | None
    teacher_tempfilled_vacancy_rate: float | None
    source_dataset_id: str
    source_dataset_version: str | None


class NormalizedThirdPartySupportRow(TypedDict):
    urn: str
    academic_year: str
    school_name: str | None
    post: str
    headcount: float | None
    source_dataset_id: str
    source_dataset_version: str | None


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    release_slug: str,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedLegacyWorkforceRow | None, str | None]:
    return normalize_legacy_workforce_row(
        raw_row,
        release_slug=release_slug,
        release_version_id=release_version_id,
        file_id=file_id,
    )


def normalize_legacy_workforce_row(
    raw_row: Mapping[str, str],
    *,
    release_slug: str,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedLegacyWorkforceRow | None, str | None]:
    urn, academic_year, rejection = _parse_urn_and_academic_year(
        raw_row,
        release_slug=release_slug,
    )
    if rejection is not None:
        return None, rejection

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

    return (
        NormalizedLegacyWorkforceRow(
            urn=urn,
            academic_year=academic_year,
            pupil_teacher_ratio=pupil_teacher_ratio,
            supply_staff_pct=supply_staff_pct,
            teachers_3plus_years_pct=teachers_3plus_years_pct,
            teacher_turnover_pct=teacher_turnover_pct,
            qts_pct=qts_pct,
            qualifications_level6_plus_pct=qualifications_level6_plus_pct,
            source_dataset_id=f"workforce:{release_version_id}",
            source_dataset_version=f"workforce:{file_id}",
        ),
        None,
    )


def normalize_teacher_characteristics_row(
    raw_row: Mapping[str, str],
    *,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedTeacherCharacteristicsRow | None, str | None]:
    urn, academic_year, rejection = _parse_urn_and_academic_year(raw_row)
    if rejection is not None:
        return None, rejection

    school_name = parse_optional_text(_pick(raw_row, "school_name"))
    if school_name is None:
        return None, "missing_school_name"

    characteristic_group = parse_optional_text(_pick(raw_row, "characteristic_group"))
    if characteristic_group is None:
        return None, "missing_characteristic_group"

    characteristic = parse_optional_text(_pick(raw_row, "characteristic"))
    if characteristic is None:
        return None, "missing_characteristic"

    grade = parse_optional_text(_pick(raw_row, "grade"))
    sex = parse_optional_text(_pick(raw_row, "sex"))
    age_group = parse_optional_text(_pick(raw_row, "age_group"))
    working_pattern = parse_optional_text(_pick(raw_row, "working_pattern"))
    qts_status = parse_optional_text(_pick(raw_row, "qts_status"))
    on_route = parse_optional_text(_pick(raw_row, "on_route"))
    ethnicity_major = parse_optional_text(_pick(raw_row, "ethnicity_major"))

    normalized_group = characteristic_group.casefold()
    if grade is None and normalized_group == "grade":
        grade = characteristic
    if sex is None and normalized_group == "sex":
        sex = characteristic
    if age_group is None and normalized_group == "age group":
        age_group = characteristic
    if working_pattern is None and normalized_group == "working pattern":
        working_pattern = characteristic
    if qts_status is None and normalized_group == "qts status":
        qts_status = characteristic
    if on_route is None and normalized_group == "on route":
        on_route = characteristic
    if (ethnicity_major is None or _looks_numeric_token(ethnicity_major)) and (
        normalized_group == "ethnicity major"
    ):
        ethnicity_major = characteristic

    raw_teacher_fte = _pick(raw_row, "full_time_equivalent")
    raw_teacher_headcount = _pick(raw_row, "headcount")
    raw_teacher_fte_pct = _pick(raw_row, "fte_school_percent")
    raw_teacher_headcount_pct = _pick(raw_row, "headcount_school_percent")
    if parse_optional_text(raw_teacher_headcount_pct) is None and _looks_numeric_token(
        _pick(raw_row, "ethnicity_major")
    ):
        raw_teacher_fte = _pick(raw_row, "ethnicity_major")
        raw_teacher_headcount = _pick(raw_row, "full_time_equivalent")
        raw_teacher_fte_pct = _pick(raw_row, "headcount")
        raw_teacher_headcount_pct = _pick(raw_row, "fte_school_percent")
        if normalized_group == "qts status" and working_pattern == characteristic:
            working_pattern = None

    try:
        teacher_fte = parse_optional_numeric(
            raw_teacher_fte,
            min_value=0.0,
        )
        teacher_headcount = parse_optional_numeric(
            raw_teacher_headcount,
            min_value=0.0,
        )
        teacher_fte_pct = parse_optional_numeric(
            raw_teacher_fte_pct,
            min_value=0.0,
            max_value=100.0,
        )
        teacher_headcount_pct = parse_optional_numeric(
            raw_teacher_headcount_pct,
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError:
        return None, "invalid_teacher_characteristics_numeric"

    return (
        NormalizedTeacherCharacteristicsRow(
            urn=urn,
            academic_year=academic_year,
            school_laestab=parse_optional_text(_pick(raw_row, "school_laestab")),
            school_name=school_name,
            school_type=parse_optional_text(_pick(raw_row, "school_type")),
            characteristic_group=characteristic_group,
            characteristic=characteristic,
            grade=grade,
            sex=sex,
            age_group=age_group,
            working_pattern=working_pattern,
            qts_status=qts_status,
            on_route=on_route,
            ethnicity_major=ethnicity_major,
            teacher_fte=teacher_fte,
            teacher_headcount=teacher_headcount,
            teacher_fte_pct=teacher_fte_pct,
            teacher_headcount_pct=teacher_headcount_pct,
            source_dataset_id=f"workforce:{release_version_id}",
            source_dataset_version=f"workforce:{file_id}",
        ),
        None,
    )


def normalize_support_staff_characteristics_row(
    raw_row: Mapping[str, str],
    *,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedSupportStaffCharacteristicsRow | None, str | None]:
    urn, academic_year, rejection = _parse_urn_and_academic_year(raw_row)
    if rejection is not None:
        return None, rejection

    school_name = parse_optional_text(_pick(raw_row, "school_name"))
    if school_name is None:
        return None, "missing_school_name"

    post = parse_optional_text(_pick(raw_row, "post"))
    if post is None:
        return None, "missing_support_staff_post"

    try:
        support_staff_fte = parse_optional_numeric(
            _pick(raw_row, "full_time_equivalent"),
            min_value=0.0,
        )
        support_staff_headcount = parse_optional_numeric(
            _pick(raw_row, "headcount"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_support_staff_numeric"

    return (
        NormalizedSupportStaffCharacteristicsRow(
            urn=urn,
            academic_year=academic_year,
            school_laestab=parse_optional_text(_pick(raw_row, "school_laestab")),
            school_name=school_name,
            school_type=parse_optional_text(_pick(raw_row, "school_type")),
            post=post,
            sex=parse_optional_text(_pick(raw_row, "sex")) or "Unknown",
            ethnicity_major=parse_optional_text(_pick(raw_row, "ethnicity_major")) or "Unknown",
            support_staff_fte=support_staff_fte,
            support_staff_headcount=support_staff_headcount,
            source_dataset_id=f"workforce:{release_version_id}",
            source_dataset_version=f"workforce:{file_id}",
        ),
        None,
    )


def normalize_teacher_pay_row(
    raw_row: Mapping[str, str],
    *,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedTeacherPayRow | None, str | None]:
    urn, academic_year, rejection = _parse_urn_and_academic_year(raw_row)
    if rejection is not None:
        return None, rejection

    try:
        teacher_headcount_all = parse_optional_numeric(
            _pick(raw_row, "headcount_all"),
            min_value=0.0,
        )
        teacher_average_mean_salary_gbp = parse_optional_numeric(
            _pick(raw_row, "average_mean"),
            min_value=0.0,
        )
        teacher_average_median_salary_gbp = parse_optional_numeric(
            _pick(raw_row, "average_median"),
            min_value=0.0,
        )
        teachers_on_leadership_pay_range_pct = parse_optional_numeric(
            _pick(raw_row, "teachers_on_leadership_pay_range_percent"),
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError:
        return None, "invalid_teacher_pay_numeric"

    return (
        NormalizedTeacherPayRow(
            urn=urn,
            academic_year=academic_year,
            teacher_headcount_all=teacher_headcount_all,
            teacher_average_mean_salary_gbp=teacher_average_mean_salary_gbp,
            teacher_average_median_salary_gbp=teacher_average_median_salary_gbp,
            teachers_on_leadership_pay_range_pct=teachers_on_leadership_pay_range_pct,
            source_dataset_id=f"workforce:{release_version_id}",
            source_dataset_version=f"workforce:{file_id}",
        ),
        None,
    )


def normalize_teacher_absence_row(
    raw_row: Mapping[str, str],
    *,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedTeacherAbsenceRow | None, str | None]:
    urn, academic_year, rejection = _parse_urn_and_academic_year(raw_row)
    if rejection is not None:
        return None, rejection

    try:
        teachers_taking_absence_count = parse_optional_numeric(
            _pick(raw_row, "total_teachers_taking_absence"),
            min_value=0.0,
        )
        teacher_absence_pct = parse_optional_numeric(
            _pick(raw_row, "percentage_taking_absence"),
            min_value=0.0,
            max_value=100.0,
        )
        teacher_absence_days_total = parse_optional_numeric(
            _pick(raw_row, "total_number_of_days_lost"),
            min_value=0.0,
        )
        teacher_absence_days_average = parse_optional_numeric(
            _pick(raw_row, "average_number_of_days_taken"),
            min_value=0.0,
        )
        teacher_absence_days_average_all_teachers = parse_optional_numeric(
            _pick(raw_row, "average_number_of_days_all_teachers"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_teacher_absence_numeric"

    return (
        NormalizedTeacherAbsenceRow(
            urn=urn,
            academic_year=academic_year,
            teachers_taking_absence_count=teachers_taking_absence_count,
            teacher_absence_pct=teacher_absence_pct,
            teacher_absence_days_total=teacher_absence_days_total,
            teacher_absence_days_average=teacher_absence_days_average,
            teacher_absence_days_average_all_teachers=teacher_absence_days_average_all_teachers,
            source_dataset_id=f"workforce:{release_version_id}",
            source_dataset_version=f"workforce:{file_id}",
        ),
        None,
    )


def normalize_teacher_vacancy_row(
    raw_row: Mapping[str, str],
    *,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedTeacherVacancyRow | None, str | None]:
    urn, academic_year, rejection = _parse_urn_and_academic_year(raw_row)
    if rejection is not None:
        return None, rejection

    try:
        teacher_vacancy_count = parse_optional_numeric(
            _pick(raw_row, "vacancy"),
            min_value=0.0,
        )
        teacher_vacancy_rate = parse_optional_numeric(
            _pick(raw_row, "rate"),
            min_value=0.0,
            max_value=100.0,
        )
        teacher_tempfilled_vacancy_count = parse_optional_numeric(
            _pick(raw_row, "tempfilled"),
            min_value=0.0,
        )
        teacher_tempfilled_vacancy_rate = parse_optional_numeric(
            _pick(raw_row, "temprate"),
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError:
        return None, "invalid_teacher_vacancy_numeric"

    return (
        NormalizedTeacherVacancyRow(
            urn=urn,
            academic_year=academic_year,
            teacher_vacancy_count=teacher_vacancy_count,
            teacher_vacancy_rate=teacher_vacancy_rate,
            teacher_tempfilled_vacancy_count=teacher_tempfilled_vacancy_count,
            teacher_tempfilled_vacancy_rate=teacher_tempfilled_vacancy_rate,
            source_dataset_id=f"workforce:{release_version_id}",
            source_dataset_version=f"workforce:{file_id}",
        ),
        None,
    )


def normalize_third_party_support_row(
    raw_row: Mapping[str, str],
    *,
    release_version_id: str,
    file_id: str,
) -> tuple[NormalizedThirdPartySupportRow | None, str | None]:
    urn, academic_year, rejection = _parse_urn_and_academic_year(raw_row)
    if rejection is not None:
        return None, rejection

    post = parse_optional_text(_pick(raw_row, "post"))
    if post is None:
        return None, "missing_third_party_post"

    try:
        headcount = parse_optional_numeric(
            _pick(raw_row, "headcount"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_third_party_support_numeric"

    return (
        NormalizedThirdPartySupportRow(
            urn=urn,
            academic_year=academic_year,
            school_name=parse_optional_text(_pick(raw_row, "school_name")),
            post=post,
            headcount=headcount,
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


def _looks_numeric_token(value: object) -> bool:
    if value is None:
        return False
    try:
        return parse_optional_numeric(value) is not None
    except ValueError:
        return False


def _parse_urn_and_academic_year(
    raw_row: Mapping[str, str],
    *,
    release_slug: str | None = None,
) -> tuple[str, str, str | None]:
    urn_raw = (_pick(raw_row, "school_urn", "urn", "URN") or "").strip()
    if len(urn_raw) != 6 or not urn_raw.isdigit():
        return "", "", "invalid_urn"

    academic_year_raw = (_pick(raw_row, "time_period", "academic_year") or "").strip()
    if not academic_year_raw and release_slug is not None:
        academic_year_raw = release_slug.replace("-", "")
    try:
        academic_year = normalize_academic_year(academic_year_raw)
    except ValueError:
        return "", "", "invalid_academic_year"
    return urn_raw, academic_year, None


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
