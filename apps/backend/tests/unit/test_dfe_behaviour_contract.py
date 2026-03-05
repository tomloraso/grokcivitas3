from __future__ import annotations

import pytest

from civitas.infrastructure.pipelines.contracts import dfe_behaviour as contract


def test_normalize_row_maps_behaviour_fields() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "100001",
            "time_period": "202324",
            "suspension": "121",
            "susp_rate": "16.4",
            "perm_excl": "1",
            "perm_excl_rate": "0.1",
        },
        release_slug="2023-24",
        release_version_id="rv-1",
        file_id="file-1",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["urn"] == "100001"
    assert normalized["academic_year"] == "2023/24"
    assert normalized["suspensions_count"] == 121
    assert normalized["suspensions_rate"] == 16.4
    assert normalized["permanent_exclusions_count"] == 1
    assert normalized["permanent_exclusions_rate"] == 0.1
    assert normalized["source_dataset_id"] == "behaviour:rv-1"
    assert normalized["source_dataset_version"] == "behaviour:file-1"


def test_normalize_row_treats_suppressed_values_as_null() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "100001",
            "time_period": "",
            "suspension": "SUPP",
            "susp_rate": ".",
            "perm_excl": "SUPP",
            "perm_excl_rate": ".",
        },
        release_slug="2023-24",
        release_version_id="rv-1",
        file_id="file-1",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2023/24"
    assert normalized["suspensions_count"] is None
    assert normalized["suspensions_rate"] is None
    assert normalized["permanent_exclusions_count"] is None
    assert normalized["permanent_exclusions_rate"] is None


def test_normalize_row_rejects_invalid_urn() -> None:
    normalized, rejection = contract.normalize_row(
        {
            "school_urn": "bad",
            "time_period": "202324",
            "suspension": "121",
            "susp_rate": "16.4",
            "perm_excl": "1",
            "perm_excl_rate": "0.1",
        },
        release_slug="2023-24",
        release_version_id="rv-1",
        file_id="file-1",
    )

    assert normalized is None
    assert rejection == "invalid_urn"


@pytest.mark.parametrize("value", ["-1", "1.2", "not-a-number"])
def test_parse_optional_count_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        contract.parse_optional_count(value)


@pytest.mark.parametrize("value", ["-0.1", "not-a-number"])
def test_parse_optional_rate_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        contract.parse_optional_rate(value)
