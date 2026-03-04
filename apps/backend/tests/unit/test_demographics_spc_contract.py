from __future__ import annotations

import pytest

from civitas.infrastructure.pipelines.contracts import demographics_spc


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "urn": "100001",
        "% of pupils known to be eligible for free school meals (Performance Tables)": "18.4",
        "% of pupils whose first language is known or believed to be other than English": "11.2",
        "% of pupils whose first language is known or believed to be English": "87.9",
        "% of pupils whose first language is unclassified": "0.9",
        "time_period": "202425",
    }
    row.update(overrides)
    return row


def test_validate_headers_accepts_required_columns() -> None:
    headers = list(_row().keys())

    column_map = demographics_spc.validate_headers(headers)

    assert column_map["urn"] == "urn"
    assert column_map["time_period"] == "time_period"


def test_validate_headers_rejects_missing_columns() -> None:
    headers = [
        "urn",
        "% of pupils known to be eligible for free school meals (Performance Tables)",
    ]

    with pytest.raises(ValueError, match="missing required headers"):
        demographics_spc.validate_headers(headers)


def test_normalize_row_accepts_compact_time_period() -> None:
    column_map = demographics_spc.validate_headers(list(_row().keys()))

    normalized, rejection = demographics_spc.normalize_row(
        _row(),
        column_map=column_map,
        release_slug="2024-25",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["urn"] == "100001"
    assert normalized["academic_year"] == "2024/25"
    assert normalized["disadvantaged_pct"] == 18.4


def test_normalize_row_derives_academic_year_from_release_slug_when_missing_time_period() -> None:
    row = _row()
    del row["time_period"]
    headers = list(row.keys())
    column_map = demographics_spc.validate_headers(headers)

    normalized, rejection = demographics_spc.normalize_row(
        row,
        column_map=column_map,
        release_slug="2023-24",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized["academic_year"] == "2023/24"


def test_normalize_row_rejects_invalid_percentage() -> None:
    column_map = demographics_spc.validate_headers(list(_row().keys()))

    normalized, rejection = demographics_spc.normalize_row(
        _row(**{"% of pupils whose first language is unclassified": "oops"}),
        column_map=column_map,
        release_slug="2024-25",
    )

    assert normalized is None
    assert rejection == "invalid_first_language_unclassified_pct"


def test_parse_release_slug_academic_year_rejects_invalid_slug() -> None:
    with pytest.raises(ValueError):
        demographics_spc.parse_release_slug_academic_year("2024")
