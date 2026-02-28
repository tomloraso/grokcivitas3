from datetime import date

import pytest

from civitas.infrastructure.pipelines.gias import (
    REQUIRED_GIAS_HEADERS,
    normalize_gias_postcode,
    normalize_gias_row,
    validate_gias_headers,
)


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "URN": "100001",
        "EstablishmentName": "Alpha Primary School",
        "TypeOfEstablishment (name)": "Community school",
        "PhaseOfEducation (name)": "Primary",
        "EstablishmentStatus (name)": "Open",
        "Postcode": "sw1a1aa",
        "Easting": "529090",
        "Northing": "179645",
        "OpenDate": "01/09/2010",
        "CloseDate": "",
        "NumberOfPupils": "312",
        "SchoolCapacity": "420",
    }
    row.update(overrides)
    return row


def test_validate_gias_headers_rejects_missing_contract_field() -> None:
    headers = [header for header in REQUIRED_GIAS_HEADERS if header != "URN"]

    with pytest.raises(ValueError, match="URN"):
        validate_gias_headers(headers)


def test_normalize_gias_postcode_formats_uppercase_with_single_space() -> None:
    assert normalize_gias_postcode(" sw1a1aa ") == "SW1A 1AA"
    assert normalize_gias_postcode("SW1A 2AB") == "SW1A 2AB"


def test_normalize_gias_row_returns_typed_record_for_valid_input() -> None:
    normalized, rejection = normalize_gias_row(_row())

    assert rejection is None
    assert normalized is not None
    assert normalized.urn == "100001"
    assert normalized.postcode == "SW1A 1AA"
    assert normalized.easting == 529090.0
    assert normalized.northing == 179645.0
    assert normalized.open_date == date(2010, 9, 1)
    assert normalized.close_date is None
    assert normalized.pupil_count == 312
    assert normalized.capacity == 420


def test_normalize_gias_row_handles_numeric_sentinels_as_null() -> None:
    normalized, rejection = normalize_gias_row(_row(NumberOfPupils="SUPP", SchoolCapacity="NE"))

    assert rejection is None
    assert normalized is not None
    assert normalized.pupil_count is None
    assert normalized.capacity is None


def test_normalize_gias_row_rejects_missing_urn() -> None:
    normalized, rejection = normalize_gias_row(_row(URN=""))

    assert normalized is None
    assert rejection == "missing_urn"


def test_normalize_gias_row_rejects_out_of_range_coordinates() -> None:
    normalized, rejection = normalize_gias_row(_row(Easting="9999999", Northing="179645"))

    assert normalized is None
    assert rejection == "invalid_coordinate_range"


def test_normalize_gias_row_rejects_invalid_date() -> None:
    normalized, rejection = normalize_gias_row(_row(OpenDate="not-a-date"))

    assert normalized is None
    assert rejection == "invalid_open_date"
