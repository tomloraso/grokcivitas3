from __future__ import annotations

import pytest

from civitas.infrastructure.pipelines.contracts import ks4_subject_performance as contract


def test_validate_headers_accepts_live_contract_order() -> None:
    contract.validate_headers(contract.KS4_REQUIRED_HEADERS)


def test_validate_headers_rejects_reordered_columns() -> None:
    with pytest.raises(ValueError, match="header order changed"):
        contract.validate_headers(tuple(reversed(contract.KS4_REQUIRED_HEADERS)))


def test_normalize_row_returns_subject_level_record() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202425",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "country_code": "E92000001",
            "country_name": "England",
            "school_laestab": "2016000",
            "school_urn": "100544",
            "school_name": "David Game College",
            "old_la_code": "201",
            "new_la_code": "E09000001",
            "la_name": "City of London",
            "version": "Revised",
            "establishment_type_group": "Independent schools",
            "pupil_count": "42",
            "qualification_type": "GCSE",
            "qualification_detailed": "GCSE (9-1) Full Course",
            "grade_structure": "9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X",
            "subject": "Art and Design",
            "discount_code": "JA2",
            "subject_discount_group": "Art & Design",
            "grade": "5",
            "number_achieving": "7",
        },
        source_file_url="https://example.com/ks4.csv",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2024/25"
    assert normalized["source_version"] == "revised"
    assert normalized["qualification_family"] == "gcse"
    assert normalized["number_achieving"] == 7


def test_normalize_row_rejects_invalid_school_urn() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202425",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "country_code": "E92000001",
            "country_name": "England",
            "school_laestab": "2016000",
            "school_urn": "ABC123",
            "school_name": "David Game College",
            "old_la_code": "201",
            "new_la_code": "E09000001",
            "la_name": "City of London",
            "version": "Revised",
            "establishment_type_group": "Independent schools",
            "pupil_count": "42",
            "qualification_type": "GCSE",
            "qualification_detailed": "GCSE (9-1) Full Course",
            "grade_structure": "9 / 8 / 7 / 6 / 5 / 4 / 3 / 2 / 1 / U / X",
            "subject": "Art and Design",
            "discount_code": "JA2",
            "subject_discount_group": "Art & Design",
            "grade": "5",
            "number_achieving": "7",
        },
        source_file_url="https://example.com/ks4.csv",
    )

    assert normalized is None
    assert rejection == "invalid_school_urn"
