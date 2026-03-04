from __future__ import annotations

from pathlib import Path

import pytest

from civitas.infrastructure.pipelines.dfe_characteristics import (
    REQUIRED_DFE_CHARACTERISTICS_HEADERS,
    normalize_dfe_characteristics_row,
    validate_dfe_characteristics_headers,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "dfe_characteristics"


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "school_urn": "100001",
        "time_period": "2024/25",
        "ptfsm6cla1a": "17.2",
        "psenelek": "13.0",
        "psenelk": "10.9",
        "psenele": "2.1",
        "ptealgrp2": "8.4",
        "ptealgrp1": "90.6",
        "ptealgrp3": "1.0",
    }
    row.update(overrides)
    return row


def test_validate_dfe_headers_rejects_missing_contract_field() -> None:
    headers = [header for header in REQUIRED_DFE_CHARACTERISTICS_HEADERS if header != "school_urn"]

    with pytest.raises(ValueError, match="school_urn"):
        validate_dfe_characteristics_headers(headers)


def test_normalize_dfe_row_returns_typed_record_for_valid_input() -> None:
    normalized, rejection = normalize_dfe_characteristics_row(_row(), source_dataset_id="dataset-1")

    assert rejection is None
    assert normalized is not None
    assert normalized.urn == "100001"
    assert normalized.academic_year == "2024/25"
    assert normalized.disadvantaged_pct == 17.2
    assert normalized.sen_pct == 13.0
    assert normalized.sen_support_pct == 10.9
    assert normalized.ehcp_pct == 2.1
    assert normalized.eal_pct == 8.4
    assert normalized.first_language_english_pct == 90.6
    assert normalized.first_language_unclassified_pct == 1.0
    assert normalized.source_dataset_id == "dataset-1"


def test_normalize_dfe_row_handles_suppressed_values_as_null() -> None:
    normalized, rejection = normalize_dfe_characteristics_row(
        _row(ptfsm6cla1a="SUPP", ptealgrp1="x"),
        source_dataset_id="dataset-1",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.disadvantaged_pct is None
    assert normalized.first_language_english_pct is None


def test_normalize_dfe_row_rejects_missing_school_urn() -> None:
    normalized, rejection = normalize_dfe_characteristics_row(
        _row(school_urn=""),
        source_dataset_id="dataset-1",
    )

    assert normalized is None
    assert rejection == "missing_urn"


def test_normalize_dfe_row_rejects_invalid_academic_year() -> None:
    normalized, rejection = normalize_dfe_characteristics_row(
        _row(time_period="2024"),
        source_dataset_id="dataset-1",
    )

    assert normalized is None
    assert rejection == "invalid_academic_year"


def test_normalize_dfe_row_supports_compact_academic_year_token() -> None:
    normalized, rejection = normalize_dfe_characteristics_row(
        _row(time_period="202425"),
        source_dataset_id="dataset-1",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.academic_year == "2024/25"


def test_normalize_dfe_row_rejects_invalid_percentage() -> None:
    normalized, rejection = normalize_dfe_characteristics_row(
        _row(psenelek="oops"),
        source_dataset_id="dataset-1",
    )

    assert normalized is None
    assert rejection == "invalid_sen_pct"


def test_dfe_fixture_is_present() -> None:
    assert (FIXTURES_DIR / "school_characteristics_valid.csv").exists()
    assert (FIXTURES_DIR / "school_characteristics_mixed.csv").exists()
