from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TypedDict

CONTRACT_VERSION = "school_financial_benchmarks.v1"

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


class NormalizedSchoolFinancialRow(TypedDict):
    urn: str
    academic_year: str
    finance_source: str
    school_laestab: str | None
    school_name: str
    trust_uid: str | None
    trust_name: str | None
    phase: str | None
    overall_phase: str | None
    admissions_policy: str | None
    urban_rural: str | None
    pupils_fte: float | None
    teachers_fte: float | None
    fsm_pct: float | None
    ehcp_pct: float | None
    sen_support_pct: float | None
    eal_pct: float | None
    total_grant_funding_gbp: float | None
    total_self_generated_funding_gbp: float | None
    total_income_gbp: float | None
    teaching_staff_costs_gbp: float | None
    supply_teaching_staff_costs_gbp: float | None
    education_support_staff_costs_gbp: float | None
    other_staff_costs_gbp: float | None
    total_staff_costs_gbp: float | None
    maintenance_improvement_costs_gbp: float | None
    premises_costs_gbp: float | None
    educational_supplies_costs_gbp: float | None
    bought_in_professional_services_costs_gbp: float | None
    catering_costs_gbp: float | None
    total_expenditure_gbp: float | None
    revenue_reserve_gbp: float | None
    in_year_balance_gbp: float | None
    source_file_url: str


def normalize_row(
    raw_row: Mapping[str, object],
    *,
    academic_year: str,
    source_file_url: str,
) -> tuple[NormalizedSchoolFinancialRow | None, str | None]:
    urn_raw = parse_optional_text(raw_row.get("URN"))
    if urn_raw is None or len(urn_raw) != 6 or not urn_raw.isdigit():
        return None, "invalid_urn"

    school_name = parse_optional_text(raw_row.get("School Name"))
    if school_name is None:
        return None, "missing_school_name"

    try:
        pupils_fte = parse_optional_numeric(
            raw_row.get("Number of pupils in academy (FTE)"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_pupils_fte"

    try:
        teachers_fte = parse_optional_numeric(
            raw_row.get("Number of teachers in academy (FTE)"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_teachers_fte"

    try:
        fsm_pct = parse_optional_numeric(
            raw_row.get("% of pupils eligible for FSM"),
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError:
        return None, "invalid_fsm_pct"

    try:
        ehcp_pct = parse_optional_numeric(
            raw_row.get("% of pupils with EHCP"),
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError:
        return None, "invalid_ehcp_pct"

    try:
        sen_support_pct = parse_optional_numeric(
            raw_row.get("% of pupil with SEN support"),
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError:
        return None, "invalid_sen_support_pct"

    try:
        eal_pct = parse_optional_numeric(
            raw_row.get("% of pupils with English as an additional language"),
            min_value=0.0,
            max_value=100.0,
        )
    except ValueError:
        return None, "invalid_eal_pct"

    try:
        total_grant_funding_gbp = parse_optional_numeric(
            raw_row.get("Total Grant Funding"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_total_grant_funding_gbp"

    try:
        total_self_generated_funding_gbp = parse_optional_numeric(
            raw_row.get("Total Self Generated Funding"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_total_self_generated_funding_gbp"

    try:
        total_income_gbp = parse_optional_numeric(
            raw_row.get("Total Income"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_total_income_gbp"

    try:
        teaching_staff_costs_gbp = parse_optional_numeric(
            raw_row.get("Teaching staff"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_teaching_staff_costs_gbp"

    try:
        supply_teaching_staff_costs_gbp = parse_optional_numeric(
            raw_row.get("Supply teaching staff"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_supply_teaching_staff_costs_gbp"

    try:
        education_support_staff_costs_gbp = parse_optional_numeric(
            raw_row.get("Education support staff"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_education_support_staff_costs_gbp"

    try:
        other_staff_costs_gbp = parse_optional_numeric(
            raw_row.get("Other staff"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_other_staff_costs_gbp"

    try:
        total_staff_costs_gbp = parse_optional_numeric(
            raw_row.get("Total Staff Costs"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_total_staff_costs_gbp"

    try:
        maintenance_improvement_costs_gbp = parse_optional_numeric(
            raw_row.get("Maintenance & Improvement Costs"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_maintenance_improvement_costs_gbp"

    try:
        premises_costs_gbp = parse_optional_numeric(
            raw_row.get("Premises Costs"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_premises_costs_gbp"

    try:
        educational_supplies_costs_gbp = parse_optional_numeric(
            raw_row.get("Total Costs of Educational Supplies"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_educational_supplies_costs_gbp"

    try:
        bought_in_professional_services_costs_gbp = parse_optional_numeric(
            raw_row.get("Costs of Brought in Professional Services"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_bought_in_professional_services_costs_gbp"

    try:
        catering_costs_gbp = parse_optional_numeric(
            raw_row.get("Catering Expenses"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_catering_costs_gbp"

    try:
        total_expenditure_gbp = parse_optional_numeric(
            raw_row.get("Total Expenditure"),
            min_value=0.0,
        )
    except ValueError:
        return None, "invalid_total_expenditure_gbp"

    try:
        revenue_reserve_gbp = parse_optional_numeric(raw_row.get("Revenue Reserve"))
    except ValueError:
        return None, "invalid_revenue_reserve_gbp"

    try:
        in_year_balance_gbp = parse_optional_numeric(raw_row.get("In year balance"))
    except ValueError:
        return None, "invalid_in_year_balance_gbp"

    return (
        NormalizedSchoolFinancialRow(
            urn=urn_raw,
            academic_year=academic_year,
            finance_source="aar",
            school_laestab=parse_optional_text(raw_row.get("LAEstab")),
            school_name=school_name,
            trust_uid=parse_optional_text(raw_row.get("UID")),
            trust_name=parse_optional_text(raw_row.get("Trust or Company Name")),
            phase=parse_optional_text(raw_row.get("Phase")),
            overall_phase=parse_optional_text(raw_row.get("Overall Phase")),
            admissions_policy=parse_optional_text(raw_row.get("Admissions policy")),
            urban_rural=parse_optional_text(raw_row.get("Urban/Rural")),
            pupils_fte=pupils_fte,
            teachers_fte=teachers_fte,
            fsm_pct=fsm_pct,
            ehcp_pct=ehcp_pct,
            sen_support_pct=sen_support_pct,
            eal_pct=eal_pct,
            total_grant_funding_gbp=total_grant_funding_gbp,
            total_self_generated_funding_gbp=total_self_generated_funding_gbp,
            total_income_gbp=total_income_gbp,
            teaching_staff_costs_gbp=teaching_staff_costs_gbp,
            supply_teaching_staff_costs_gbp=supply_teaching_staff_costs_gbp,
            education_support_staff_costs_gbp=education_support_staff_costs_gbp,
            other_staff_costs_gbp=other_staff_costs_gbp,
            total_staff_costs_gbp=total_staff_costs_gbp,
            maintenance_improvement_costs_gbp=maintenance_improvement_costs_gbp,
            premises_costs_gbp=premises_costs_gbp,
            educational_supplies_costs_gbp=educational_supplies_costs_gbp,
            bought_in_professional_services_costs_gbp=(bought_in_professional_services_costs_gbp),
            catering_costs_gbp=catering_costs_gbp,
            total_expenditure_gbp=total_expenditure_gbp,
            revenue_reserve_gbp=revenue_reserve_gbp,
            in_year_balance_gbp=in_year_balance_gbp,
            source_file_url=source_file_url,
        ),
        None,
    )


def parse_optional_numeric(
    value: object,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float | None:
    if value is None:
        return None

    if isinstance(value, bool):
        raise ValueError("unsupported numeric value type")
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


def parse_optional_text(value: object) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    if token.casefold() in NULL_TOKENS:
        return None
    return token
