from __future__ import annotations

import pytest

from civitas.infrastructure.pipelines.contracts import demographics_sen


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "URN": "100001",
        "time_period": "202425",
        "Total pupils": "250",
        "SEN support": "37",
        "EHC plan": "11",
    }
    row.update(overrides)
    return row


def test_validate_headers_accepts_required_columns() -> None:
    column_map = demographics_sen.validate_headers(list(_row().keys()))

    assert column_map["urn"] == "URN"
    assert column_map["time_period"] == "time_period"


def test_validate_headers_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="missing required headers"):
        demographics_sen.validate_headers(["URN", "time_period"])


def test_normalize_row_calculates_percentages() -> None:
    column_map = demographics_sen.validate_headers(list(_row().keys()))

    normalized, rejection = demographics_sen.normalize_row(_row(), column_map=column_map)

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2024/25"
    assert normalized["total_pupils"] == 250
    assert normalized["sen_support_pct"] == pytest.approx(14.8)
    assert normalized["ehcp_pct"] == pytest.approx(4.4)


def test_normalize_row_sets_percentages_null_when_total_pupils_zero() -> None:
    column_map = demographics_sen.validate_headers(list(_row().keys()))

    normalized, rejection = demographics_sen.normalize_row(
        _row(**{"Total pupils": "0"}),
        column_map=column_map,
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["sen_support_pct"] is None
    assert normalized["ehcp_pct"] is None


def test_normalize_row_rejects_invalid_total_pupils() -> None:
    column_map = demographics_sen.validate_headers(list(_row().keys()))

    normalized, rejection = demographics_sen.normalize_row(
        _row(**{"Total pupils": "oops"}),
        column_map=column_map,
    )

    assert normalized is None
    assert rejection == "invalid_total_pupils"


def test_normalize_row_rejects_out_of_range_percentage() -> None:
    column_map = demographics_sen.validate_headers(list(_row().keys()))

    normalized, rejection = demographics_sen.normalize_row(
        _row(**{"SEN support": "999"}),
        column_map=column_map,
    )

    assert normalized is None
    assert rejection == "invalid_sen_support"
