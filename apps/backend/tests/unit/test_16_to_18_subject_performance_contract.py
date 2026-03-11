from __future__ import annotations

import pytest

from civitas.infrastructure.pipelines.contracts import (
    sixteen_to_eighteen_subject_performance as contract,
)


def test_validate_headers_accepts_live_contract_order() -> None:
    contract.validate_headers(contract.REQUIRED_HEADERS)


def test_validate_headers_rejects_reordered_columns() -> None:
    with pytest.raises(ValueError, match="header order changed"):
        contract.validate_headers(tuple(reversed(contract.REQUIRED_HEADERS)))


def test_normalize_row_normalizes_spelling_and_family() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202425",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "country_code": "E92000001",
            "country_name": "England",
            "version": "Revised",
            "old_la_code": "201",
            "new_la_code": "E09000001",
            "la_name": "City of London",
            "school_name": "City of London School for Girls",
            "school_urn": "100001",
            "school_laestab": "2016005",
            "exam_cohort": "A level",
            "qualification_detailed": "GCE A level",
            "qualification_level": "3",
            "a_level_equivelent_size": "1",
            "gcse_equivelent_size": "4",
            "grade_structure": "*,A,B,C,D,E",
            "subject": "All subjects",
            "grade": "A*",
            "entries_count": "131",
        },
        source_file_url="https://example.com/16-to-18.csv",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2024/25"
    assert normalized["source_version"] == "revised"
    assert normalized["qualification_family"] == "a_level"
    assert normalized["a_level_equivalent_size"] == pytest.approx(1.0)
    assert normalized["gcse_equivalent_size"] == pytest.approx(4.0)


def test_normalize_row_rejects_missing_exam_cohort() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "time_period": "202425",
            "time_identifier": "Academic year",
            "geographic_level": "School",
            "country_code": "E92000001",
            "country_name": "England",
            "version": "Revised",
            "old_la_code": "201",
            "new_la_code": "E09000001",
            "la_name": "City of London",
            "school_name": "City of London School for Girls",
            "school_urn": "100001",
            "school_laestab": "2016005",
            "exam_cohort": "",
            "qualification_detailed": "GCE A level",
            "qualification_level": "3",
            "a_level_equivelent_size": "1",
            "gcse_equivelent_size": "4",
            "grade_structure": "*,A,B,C,D,E",
            "subject": "All subjects",
            "grade": "A*",
            "entries_count": "131",
        },
        source_file_url="https://example.com/16-to-18.csv",
    )

    assert normalized is None
    assert rejection == "missing_exam_cohort"
