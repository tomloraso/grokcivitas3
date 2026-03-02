from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from civitas.infrastructure.pipelines.ofsted_timeline import (
    REQUIRED_OFSTED_TIMELINE_HISTORICAL_HEADERS,
    REQUIRED_OFSTED_TIMELINE_YTD_HEADERS,
    SCHEMA_VERSION_HISTORICAL_2015_2019,
    SCHEMA_VERSION_YTD,
    extract_ofsted_timeline_asset_urls,
    normalize_ofsted_timeline_row,
    validate_ofsted_timeline_headers,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "ofsted_timeline"


def _ytd_row(**overrides: str) -> dict[str, str]:
    row = {
        "URN": "100001",
        "Inspection number": "INSP-1",
        "Inspection type": "S5 Inspection",
        "Inspection start date": "12/11/2025",
        "Inspection end date": "",
        "Publication date": "12/01/2026",
        "Latest OEIF overall effectiveness": "1",
        "Ungraded inspection overall outcome": "",
        "Category of concern": "",
    }
    row.update(overrides)
    return row


def _historical_row(**overrides: str) -> dict[str, str]:
    row = {
        "Academic year": "2015/16",
        "URN": "100001",
        "Inspection number": "HIST-1",
        "Inspection start date": "14/09/2015",
        "Publication date": "01/10/2015",
        "Overall effectiveness": "Good",
        "Category of concern": "",
    }
    row.update(overrides)
    return row


def test_validate_ofsted_timeline_headers_rejects_missing_ytd_fields() -> None:
    headers = [h for h in REQUIRED_OFSTED_TIMELINE_YTD_HEADERS if h != "Inspection number"]

    with pytest.raises(ValueError, match="Inspection number"):
        validate_ofsted_timeline_headers(headers, schema_version=SCHEMA_VERSION_YTD)


def test_validate_ofsted_timeline_headers_rejects_missing_historical_fields() -> None:
    headers = [h for h in REQUIRED_OFSTED_TIMELINE_HISTORICAL_HEADERS if h != "Academic year"]

    with pytest.raises(ValueError, match="Academic year"):
        validate_ofsted_timeline_headers(
            headers,
            schema_version=SCHEMA_VERSION_HISTORICAL_2015_2019,
        )


def test_extract_ofsted_timeline_asset_urls_picks_latest_all_inspections() -> None:
    html_payload = """
    <html>
      <body>
        <a href="https://assets.publishing.service.gov.uk/media/old/Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_30_Nov_2025.csv">older-all</a>
        <a href="https://assets.publishing.service.gov.uk/media/new/Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_31_Jan_2026.csv">latest-all</a>
        <a href="https://assets.publishing.service.gov.uk/media/latest/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv">latest-only</a>
        <a href="https://assets.publishing.service.gov.uk/media/historical/Management_information_-_state-funded_schools_1_September_2015_to_31_August_2019.csv">historical</a>
      </body>
    </html>
    """

    all_url, latest_url, historical_url = extract_ofsted_timeline_asset_urls(html_payload)

    assert all_url.endswith("published_by_31_Jan_2026.csv")
    assert latest_url.endswith("latest_inspections_as_at_31_Jan_2026.csv")
    assert historical_url is not None
    assert historical_url.endswith("1_September_2015_to_31_August_2019.csv")


def test_normalize_ytd_row_returns_typed_record_for_graded_value() -> None:
    normalized, rejection = normalize_ofsted_timeline_row(
        _ytd_row(),
        source_schema_version=SCHEMA_VERSION_YTD,
        source_asset_url="https://assets.publishing.service.gov.uk/media/new/ytd.csv",
        source_asset_month="2026-01",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.urn == "100001"
    assert normalized.inspection_number == "INSP-1"
    assert normalized.inspection_start_date == date(2025, 11, 12)
    assert normalized.publication_date == date(2026, 1, 12)
    assert normalized.overall_effectiveness_code == "1"
    assert normalized.overall_effectiveness_label == "Outstanding"
    assert normalized.headline_outcome_text is None


def test_normalize_historical_row_maps_textual_overall_effectiveness() -> None:
    normalized, rejection = normalize_ofsted_timeline_row(
        _historical_row(),
        source_schema_version=SCHEMA_VERSION_HISTORICAL_2015_2019,
        source_asset_url="https://assets.publishing.service.gov.uk/media/historical/file.csv",
        source_asset_month=None,
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.inspection_number == "HIST-1"
    assert normalized.overall_effectiveness_code == "2"
    assert normalized.overall_effectiveness_label == "Good"


def test_normalize_row_supports_ungraded_outcome_text() -> None:
    normalized, rejection = normalize_ofsted_timeline_row(
        _ytd_row(
            **{
                "Latest OEIF overall effectiveness": "",
                "Ungraded inspection overall outcome": "Strong progress",
            }
        ),
        source_schema_version=SCHEMA_VERSION_YTD,
        source_asset_url="https://assets.publishing.service.gov.uk/media/new/ytd.csv",
        source_asset_month="2026-01",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.overall_effectiveness_code is None
    assert normalized.overall_effectiveness_label is None
    assert normalized.headline_outcome_text == "Strong progress"


def test_normalize_row_rejects_missing_inspection_number() -> None:
    normalized, rejection = normalize_ofsted_timeline_row(
        _ytd_row(**{"Inspection number": ""}),
        source_schema_version=SCHEMA_VERSION_YTD,
        source_asset_url="https://assets.publishing.service.gov.uk/media/new/ytd.csv",
        source_asset_month="2026-01",
    )

    assert normalized is None
    assert rejection == "missing_inspection_number"


def test_normalize_row_rejects_invalid_inspection_start_date() -> None:
    normalized, rejection = normalize_ofsted_timeline_row(
        _ytd_row(**{"Inspection start date": "not-a-date"}),
        source_schema_version=SCHEMA_VERSION_YTD,
        source_asset_url="https://assets.publishing.service.gov.uk/media/new/ytd.csv",
        source_asset_month="2026-01",
    )

    assert normalized is None
    assert rejection == "invalid_inspection_start_date"


def test_ofsted_timeline_fixtures_are_present() -> None:
    assert (FIXTURES_DIR / "all_inspections_ytd_mixed.csv").exists()
    assert (FIXTURES_DIR / "all_inspections_historical_2015_2019_mixed.csv").exists()
