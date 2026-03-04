from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from civitas.infrastructure.pipelines.police_crime_context import (
    REQUIRED_POLICE_STREET_HEADERS,
    extract_latest_police_archive_url,
    normalize_police_street_row,
    validate_police_street_headers,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "police_crime_context"


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "Crime type": "violent-crime",
        "Longitude": "-0.1411",
        "Latitude": "51.5011",
        "Month": "2026-01",
    }
    row.update(overrides)
    return row


def test_validate_police_headers_rejects_missing_contract_field() -> None:
    headers = [header for header in REQUIRED_POLICE_STREET_HEADERS if header != "Crime type"]

    with pytest.raises(ValueError, match="Crime type"):
        validate_police_street_headers(headers)


def test_extract_latest_police_archive_url_picks_latest_month() -> None:
    html_payload = """
    <a href="/data/archive/2025-12.zip">2025-12</a>
    <a href="/data/archive/2026-01.zip">2026-01</a>
    """

    archive_url = extract_latest_police_archive_url(html_payload)

    assert archive_url == "https://data.police.uk/data/archive/2026-01.zip"


def test_normalize_police_row_returns_typed_record_for_valid_input() -> None:
    normalized, rejection = normalize_police_street_row(_row())

    assert rejection is None
    assert normalized is not None
    assert normalized.month == date(2026, 1, 1)
    assert normalized.crime_category == "violent-crime"
    assert normalized.longitude == -0.1411
    assert normalized.latitude == 51.5011


def test_normalize_police_row_rejects_missing_longitude() -> None:
    normalized, rejection = normalize_police_street_row(_row(Longitude=""))

    assert normalized is None
    assert rejection == "missing_longitude"


def test_normalize_police_row_rejects_invalid_month() -> None:
    normalized, rejection = normalize_police_street_row(_row(Month="2026-99"))

    assert normalized is None
    assert rejection == "invalid_month"


def test_normalize_police_row_rejects_invalid_latitude() -> None:
    normalized, rejection = normalize_police_street_row(_row(Latitude="100.0"))

    assert normalized is None
    assert rejection == "invalid_latitude"


def test_police_crime_fixture_is_present() -> None:
    assert (FIXTURES_DIR / "2026-01-example-street.csv").exists()
