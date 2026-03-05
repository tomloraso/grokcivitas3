from __future__ import annotations

import pytest

from civitas.infrastructure.pipelines.contracts import dfe_attendance as contract


def test_normalize_row_maps_attendance_fields() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "100001",
            "time_period": "202324",
            "sess_overall_percent": "6.1",
            "enrolments_pa_10_exact_percent": "14.2",
        },
        release_slug="2023-24",
        release_version_id="rv-1",
        file_id="file-1",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["urn"] == "100001"
    assert normalized["academic_year"] == "2023/24"
    assert normalized["overall_absence_pct"] == 6.1
    assert normalized["overall_attendance_pct"] == pytest.approx(93.9)
    assert normalized["persistent_absence_pct"] == 14.2
    assert normalized["source_dataset_id"] == "attendance:rv-1"
    assert normalized["source_dataset_version"] == "attendance:file-1"


def test_normalize_row_treats_suppressed_values_as_null() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "100001",
            "time_period": "",
            "sess_overall_percent": "SUPP",
            "enrolments_pa_10_exact_percent": ".",
        },
        release_slug="2023-24",
        release_version_id="rv-1",
        file_id="file-1",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2023/24"
    assert normalized["overall_absence_pct"] is None
    assert normalized["overall_attendance_pct"] is None
    assert normalized["persistent_absence_pct"] is None


def test_normalize_row_rejects_invalid_urn() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "bad",
            "time_period": "202324",
            "sess_overall_percent": "6.1",
            "enrolments_pa_10_exact_percent": "14.2",
        },
        release_slug="2023-24",
        release_version_id="rv-1",
        file_id="file-1",
    )

    assert normalized is None
    assert rejection == "invalid_urn"


@pytest.mark.parametrize("value", ["-0.1", "101", "not-a-number"])
def test_parse_optional_percentage_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        contract.parse_optional_percentage(value, allow_over_100=False)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("202324", "2023/24"),
        ("2023/24", "2023/24"),
        ("2023/2024", "2023/24"),
    ],
)
def test_normalize_academic_year(raw_value: str, expected: str) -> None:
    assert contract.normalize_academic_year(raw_value) == expected
