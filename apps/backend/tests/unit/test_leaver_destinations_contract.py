from __future__ import annotations

import pytest

from civitas.infrastructure.pipelines.contracts import leaver_destinations as contract


def test_validate_headers_accepts_proved_ks4_and_16_to_18_contracts() -> None:
    contract.validate_headers(
        destination_stage="ks4",
        headers=contract.KS4_REQUIRED_HEADERS,
    )
    contract.validate_headers(
        destination_stage="16_to_18",
        headers=contract.STUDY_16_TO_18_REQUIRED_HEADERS,
    )


def test_validate_headers_rejects_header_drift_and_order_changes() -> None:
    with pytest.raises(ValueError, match="unexpected headers: extra_column"):
        contract.validate_headers(
            destination_stage="ks4",
            headers=(*contract.KS4_REQUIRED_HEADERS, "extra_column"),
        )

    with pytest.raises(ValueError, match="header order changed"):
        contract.validate_headers(
            destination_stage="16_to_18",
            headers=(
                contract.STUDY_16_TO_18_REQUIRED_HEADERS[1],
                contract.STUDY_16_TO_18_REQUIRED_HEADERS[0],
                *contract.STUDY_16_TO_18_REQUIRED_HEADERS[2:],
            ),
        )


def test_normalize_row_maps_ks4_fields_and_suppression_tokens() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202223",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "school_laestab": "2136007",
            "school_urn": "100001",
            "school_name": "Alpha School",
            "admission_policy": "Comprehensive",
            "entry_gender": "Mixed",
            "institution_group": "Local authority maintained schools",
            "institution_type": "Community school",
            "breakdown_topic": "Total",
            "breakdown": "Total",
            "data_type": "Percentage",
            "cohort": "118",
            "overall": "92.4",
            "education": "61.0",
            "fe": "18.0",
            "ssf": "c",
            "sfc": "",
            "other_edu": "4.0",
            "appren": "7.3",
            "all_work": "17.5",
            "all_notsust": "3.1",
            "all_unknown": "4.5",
        },
        destination_stage="ks4",
        source_file_url="https://example.com/ks4.csv",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2022/23"
    assert normalized["destination_stage"] == "ks4"
    assert normalized["qualification_group"] is None
    assert normalized["qualification_level"] is None
    assert normalized["overall_value"] == 92.4
    assert normalized["education_value"] == 61.0
    assert normalized["fe_value"] == 18.0
    assert normalized["school_sixth_form_value"] is None
    assert normalized["sixth_form_college_value"] is None
    assert normalized["apprenticeship_value"] == 7.3
    assert normalized["employment_value"] == 17.5


def test_normalize_row_maps_16_to_18_qualification_and_higher_education_fields() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202223",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "school_laestab": "2013614",
            "school_urn": "100002",
            "school_name": "Beta Sixth Form",
            "admission_policy": "Not applicable",
            "entry_gender": "Mixed",
            "institution_group": "Academies",
            "institution_type": "Academy converter",
            "cohort_level_group": "Total",
            "cohort_level": "Total",
            "breakdown_topic": "Total",
            "breakdown": "Total",
            "data_type": "Number of students",
            "cohort": "90",
            "overall": "80",
            "education": "56",
            "he": "31",
            "fe": "18",
            "other_edu": "7",
            "appren": "10",
            "all_work": "14",
            "all_notsust": "6",
            "all_unknown": "10",
        },
        destination_stage="16_to_18",
        source_file_url="https://example.com/16-to-18.csv",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2022/23"
    assert normalized["destination_stage"] == "16_to_18"
    assert normalized["qualification_group"] == "Total"
    assert normalized["qualification_level"] == "Total"
    assert normalized["higher_education_value"] == 31.0
    assert normalized["fe_value"] == 18.0
    assert normalized["other_education_value"] == 7.0
    assert normalized["cohort_count"] == 90


def test_normalize_row_rejects_invalid_identifiers_and_data_types() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202223",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "school_laestab": "2136007",
            "school_urn": "ABC123",
            "school_name": "Alpha School",
            "breakdown_topic": "Total",
            "breakdown": "Total",
            "data_type": "Percentage",
        },
        destination_stage="ks4",
        source_file_url="https://example.com/ks4.csv",
    )
    assert normalized is None
    assert rejection == "invalid_school_urn"

    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202223",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "school_laestab": "2136007",
            "school_urn": "100001",
            "school_name": "Alpha School",
            "breakdown_topic": "Total",
            "breakdown": "Total",
            "data_type": "Count",
        },
        destination_stage="ks4",
        source_file_url="https://example.com/ks4.csv",
    )
    assert normalized is None
    assert rejection == "invalid_data_type"
