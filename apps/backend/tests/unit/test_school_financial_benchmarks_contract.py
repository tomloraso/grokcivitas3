from __future__ import annotations

from civitas.infrastructure.pipelines.contracts import school_financial_benchmarks as contract


def test_normalize_row_maps_finance_fields() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "LAEstab": "213/6007",
            "URN": "123456",
            "School Name": "Example Academy",
            "UID": "5712",
            "Trust or Company Name": "Example Trust",
            "Overall Phase": "Primary",
            "Phase": "Primary",
            "Admissions policy": "Not applicable",
            "Urban/Rural": "Urban major conurbation",
            "Number of pupils in academy (FTE)": "312.5",
            "Number of teachers in academy (FTE)": "18.4",
            "% of pupils eligible for FSM": "16.9",
            "% of pupils with EHCP": "2.1",
            "% of pupil with SEN support": "13.0",
            "% of pupils with English as an additional language": "8.4",
            "Total Grant Funding": "1950000",
            "Total Self Generated Funding": "120000",
            "Total Income": "2070000",
            "Teaching staff": "1015000",
            "Supply teaching staff": "24500",
            "Education support staff": "332000",
            "Other staff": "188000",
            "Total Staff Costs": "1559500",
            "Maintenance & Improvement Costs": "90500",
            "Premises Costs": "118000",
            "Total Costs of Educational Supplies": "56000",
            "Costs of Brought in Professional Services": "42000",
            "Catering Expenses": "64000",
            "Total Expenditure": "2030000",
            "Revenue Reserve": "275000",
            "In year balance": "40000",
        },
        academic_year="2023/24",
        source_file_url="https://example.com/AAR_2023-24_download.xlsx",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["urn"] == "123456"
    assert normalized["academic_year"] == "2023/24"
    assert normalized["finance_source"] == "aar"
    assert normalized["school_laestab"] == "213/6007"
    assert normalized["school_name"] == "Example Academy"
    assert normalized["trust_uid"] == "5712"
    assert normalized["trust_name"] == "Example Trust"
    assert normalized["phase"] == "Primary"
    assert normalized["overall_phase"] == "Primary"
    assert normalized["admissions_policy"] == "Not applicable"
    assert normalized["urban_rural"] == "Urban major conurbation"
    assert normalized["pupils_fte"] == 312.5
    assert normalized["teachers_fte"] == 18.4
    assert normalized["fsm_pct"] == 16.9
    assert normalized["ehcp_pct"] == 2.1
    assert normalized["sen_support_pct"] == 13.0
    assert normalized["eal_pct"] == 8.4
    assert normalized["total_grant_funding_gbp"] == 1950000.0
    assert normalized["total_self_generated_funding_gbp"] == 120000.0
    assert normalized["total_income_gbp"] == 2070000.0
    assert normalized["teaching_staff_costs_gbp"] == 1015000.0
    assert normalized["supply_teaching_staff_costs_gbp"] == 24500.0
    assert normalized["education_support_staff_costs_gbp"] == 332000.0
    assert normalized["other_staff_costs_gbp"] == 188000.0
    assert normalized["total_staff_costs_gbp"] == 1559500.0
    assert normalized["maintenance_improvement_costs_gbp"] == 90500.0
    assert normalized["premises_costs_gbp"] == 118000.0
    assert normalized["educational_supplies_costs_gbp"] == 56000.0
    assert normalized["bought_in_professional_services_costs_gbp"] == 42000.0
    assert normalized["catering_costs_gbp"] == 64000.0
    assert normalized["total_expenditure_gbp"] == 2030000.0
    assert normalized["revenue_reserve_gbp"] == 275000.0
    assert normalized["in_year_balance_gbp"] == 40000.0
    assert normalized["source_file_url"] == "https://example.com/AAR_2023-24_download.xlsx"


def test_normalize_row_handles_blank_and_suppressed_numeric_cells() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "URN": "123456",
            "School Name": "Example Academy",
            "Number of pupils in academy (FTE)": "",
            "Number of teachers in academy (FTE)": "SUPP",
            "% of pupils eligible for FSM": ".",
            "% of pupils with EHCP": "n/a",
            "% of pupil with SEN support": "x",
            "% of pupils with English as an additional language": "na",
            "Total Grant Funding": "",
            "Total Self Generated Funding": "SUPP",
            "Total Income": "n/a",
            "Teaching staff": ".",
            "Supply teaching staff": "x",
            "Education support staff": "na",
            "Other staff": "SUPP",
            "Total Staff Costs": "",
            "Maintenance & Improvement Costs": "n/a",
            "Premises Costs": "SUPP",
            "Total Costs of Educational Supplies": "",
            "Costs of Brought in Professional Services": ".",
            "Catering Expenses": "x",
            "Total Expenditure": "na",
            "Revenue Reserve": "",
            "In year balance": "SUPP",
        },
        academic_year="2023/24",
        source_file_url="https://example.com/AAR_2023-24_download.xlsx",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["pupils_fte"] is None
    assert normalized["teachers_fte"] is None
    assert normalized["fsm_pct"] is None
    assert normalized["ehcp_pct"] is None
    assert normalized["sen_support_pct"] is None
    assert normalized["eal_pct"] is None
    assert normalized["total_grant_funding_gbp"] is None
    assert normalized["total_self_generated_funding_gbp"] is None
    assert normalized["total_income_gbp"] is None
    assert normalized["teaching_staff_costs_gbp"] is None
    assert normalized["supply_teaching_staff_costs_gbp"] is None
    assert normalized["education_support_staff_costs_gbp"] is None
    assert normalized["other_staff_costs_gbp"] is None
    assert normalized["total_staff_costs_gbp"] is None
    assert normalized["maintenance_improvement_costs_gbp"] is None
    assert normalized["premises_costs_gbp"] is None
    assert normalized["educational_supplies_costs_gbp"] is None
    assert normalized["bought_in_professional_services_costs_gbp"] is None
    assert normalized["catering_costs_gbp"] is None
    assert normalized["total_expenditure_gbp"] is None
    assert normalized["revenue_reserve_gbp"] is None
    assert normalized["in_year_balance_gbp"] is None


def test_normalize_row_rejects_invalid_values() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "URN": "ABC123",
            "School Name": "Example Academy",
        },
        academic_year="2023/24",
        source_file_url="https://example.com/AAR_2023-24_download.xlsx",
    )
    assert normalized is None
    assert rejection == "invalid_urn"

    normalized, rejection = contract.normalize_row(
        {
            "URN": "123456",
            "School Name": "   ",
        },
        academic_year="2023/24",
        source_file_url="https://example.com/AAR_2023-24_download.xlsx",
    )
    assert normalized is None
    assert rejection == "missing_school_name"

    normalized, rejection = contract.normalize_row(
        {
            "URN": "123456",
            "School Name": "Example Academy",
            "% of pupils eligible for FSM": "101.0",
        },
        academic_year="2023/24",
        source_file_url="https://example.com/AAR_2023-24_download.xlsx",
    )
    assert normalized is None
    assert rejection == "invalid_fsm_pct"
