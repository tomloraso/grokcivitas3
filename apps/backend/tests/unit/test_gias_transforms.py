import csv
from datetime import date
from pathlib import Path

import pytest

from civitas.infrastructure.pipelines.gias import (
    GIAS_CSV_ENCODING,
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
        "SchoolWebsite": "alphaprimary.example",
        "TelephoneNum": "+44 20 7946 0123",
        "HeadTitle (name)": "Dr",
        "HeadFirstName": "Ada",
        "HeadLastName": "Lovelace",
        "HeadPreferredJobTitle": "Headteacher",
        "Street": "1 Test Street",
        "Locality": "Westminster",
        "Address3": "",
        "Town": "London",
        "County (name)": "Greater London",
        "StatutoryLowAge": "4",
        "StatutoryHighAge": "11",
        "Gender (name)": "Mixed",
        "ReligiousCharacter (name)": "None",
        "Diocese (name)": "",
        "AdmissionsPolicy (name)": "Not applicable",
        "OfficialSixthForm (name)": "Does not have a sixth form",
        "NurseryProvision (name)": "No Nursery Classes",
        "Boarders (name)": "No boarders",
        "PercentageFSM": "12.4",
        "Trusts (name)": "",
        "TrustSchoolFlag (name)": "Not applicable",
        "Federations (name)": "",
        "FederationFlag (name)": "Not applicable",
        "LA (name)": "Westminster",
        "LA (code)": "213",
        "UrbanRural (name)": "Urban major conurbation",
        "NumberOfBoys": "155",
        "NumberOfGirls": "157",
        "LSOA (code)": "E01004736",
        "LSOA (name)": "Westminster 018A",
        "LastChangedDate": "15/01/2026",
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
    normalized, rejection, warnings = normalize_gias_row(_row())

    assert rejection is None
    assert normalized is not None
    assert warnings == ()
    assert normalized.urn == "100001"
    assert normalized.postcode == "SW1A 1AA"
    assert normalized.easting == 529090.0
    assert normalized.northing == 179645.0
    assert normalized.open_date == date(2010, 9, 1)
    assert normalized.close_date is None
    assert normalized.pupil_count == 312
    assert normalized.capacity == 420
    assert normalized.website == "https://alphaprimary.example"
    assert normalized.telephone == "+442079460123"
    assert normalized.statutory_low_age == 4
    assert normalized.statutory_high_age == 11
    assert normalized.fsm_pct_gias == pytest.approx(12.4)
    assert normalized.last_changed_date == date(2026, 1, 15)


def test_normalize_gias_row_accepts_hyphenated_uk_dates() -> None:
    normalized, rejection, warnings = normalize_gias_row(
        _row(OpenDate="01-04-2011", CloseDate="31-08-2020")
    )

    assert rejection is None
    assert normalized is not None
    assert warnings == ()
    assert normalized.open_date == date(2011, 4, 1)
    assert normalized.close_date == date(2020, 8, 31)


def test_normalize_gias_row_handles_numeric_sentinels_as_null() -> None:
    normalized, rejection, warnings = normalize_gias_row(
        _row(NumberOfPupils="SUPP", SchoolCapacity="NE")
    )

    assert rejection is None
    assert normalized is not None
    assert warnings == ()
    assert normalized.pupil_count is None
    assert normalized.capacity is None


def test_normalize_gias_row_rejects_missing_urn() -> None:
    normalized, rejection, warnings = normalize_gias_row(_row(URN=""))

    assert normalized is None
    assert rejection == "missing_urn"
    assert warnings == ()


def test_normalize_gias_row_rejects_out_of_range_coordinates() -> None:
    normalized, rejection, warnings = normalize_gias_row(_row(Easting="9999999", Northing="179645"))

    assert normalized is None
    assert rejection == "invalid_coordinate_range"
    assert warnings == ()


def test_normalize_gias_row_rejects_invalid_date() -> None:
    normalized, rejection, warnings = normalize_gias_row(_row(OpenDate="not-a-date"))

    assert normalized is None
    assert rejection == "invalid_open_date"
    assert warnings == ()


def test_normalize_gias_row_coerces_invalid_optional_fields_to_null_with_warning() -> None:
    normalized, rejection, warnings = normalize_gias_row(
        _row(
            SchoolWebsite="not a url",
            TelephoneNum="()",
            StatutoryLowAge="30",
            PercentageFSM="101",
            NumberOfBoys="not-a-number",
            LastChangedDate="not-a-date",
        )
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.website is None
    assert normalized.telephone is None
    assert normalized.statutory_low_age is None
    assert normalized.fsm_pct_gias is None
    assert normalized.number_of_boys is None
    assert normalized.last_changed_date is None
    assert {(warning["field_name"], warning["reason_code"]) for warning in warnings} == {
        ("SchoolWebsite", "invalid_website"),
        ("TelephoneNum", "invalid_telephone"),
        ("StatutoryLowAge", "age_out_of_range"),
        ("PercentageFSM", "percentage_out_of_range"),
        ("NumberOfBoys", "invalid_integer"),
        ("LastChangedDate", "invalid_date"),
    }


def test_csv_with_cp1252_characters_parses_without_error(tmp_path: Path) -> None:
    fixture = tmp_path / "edubasealldata_cp1252.csv"
    headers = ",".join(REQUIRED_GIAS_HEADERS)
    row = ",".join(
        [
            "300001",
            "St Mary\u2019s Church of England Primary",
            "Community school",
            "Primary",
            "Open",
            "N1 9GU",
            "531265",
            "184637",
            "01/09/2012",
            "",
            "280",
            "360",
            "stmarys.example",
            "020 7946 0000",
            "Mrs",
            "Jane",
            "Smith",
            "Headteacher",
            "1 Church Lane",
            "",
            "",
            "London",
            "Greater London",
            "4",
            "11",
            "Mixed",
            "Church of England",
            "London",
            "Not applicable",
            "Does not have a sixth form",
            "No Nursery Classes",
            "No boarders",
            "14.2",
            "",
            "Not applicable",
            "",
            "Not applicable",
            "Islington",
            "206",
            "Urban major conurbation",
            "140",
            "140",
            "E01002771",
            "Islington 001A",
            "15/01/2026",
        ]
    )
    fixture.write_bytes(f"{headers}\n{row}\n".encode(GIAS_CSV_ENCODING))

    with pytest.raises(UnicodeDecodeError):
        fixture.read_text(encoding="utf-8")

    with fixture.open("r", encoding=GIAS_CSV_ENCODING, newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert len(rows) == 1
    normalized, rejection, warnings = normalize_gias_row(rows[0])
    assert rejection is None
    assert normalized is not None
    assert warnings == ()
    assert "\u2019" in normalized.name
