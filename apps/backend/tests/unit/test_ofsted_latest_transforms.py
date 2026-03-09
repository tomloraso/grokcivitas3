from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from civitas.infrastructure.pipelines.ofsted_latest import (
    REQUIRED_OFSTED_LATEST_HEADERS,
    extract_latest_ofsted_asset_url,
    normalize_ofsted_latest_row,
    validate_ofsted_latest_headers,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "ofsted_latest"


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "URN": "100001",
        "Web Link (opens in new window)": (
            "http://www.ofsted.gov.uk/inspection-reports/find-inspection-report/provider/ELS/100001"
        ),
        "Inspection start date": "15/01/2026",
        "Publication date": "20/02/2026",
        "Latest OEIF overall effectiveness": "2",
        "Inspection start date of latest OEIF graded inspection": "15/01/2026",
        "Publication date of latest OEIF graded inspection": "20/02/2026",
        "Latest OEIF quality of education": "2",
        "Latest OEIF behaviour and attitudes": "2",
        "Latest OEIF personal development": "2",
        "Latest OEIF effectiveness of leadership and management": "2",
        "Date of latest ungraded inspection": "",
        "Ungraded inspection publication date": "",
        "Ungraded inspection overall outcome": "",
    }
    row.update(overrides)
    return row


def test_validate_ofsted_headers_rejects_missing_contract_field() -> None:
    headers = [header for header in REQUIRED_OFSTED_LATEST_HEADERS if header != "URN"]

    with pytest.raises(ValueError, match="URN"):
        validate_ofsted_latest_headers(headers)


def test_extract_latest_ofsted_asset_url_returns_newest_dated_asset_link() -> None:
    html_payload = """
    <html>
      <body>
        <a href="https://example.com/not-ofsted.csv">Skip</a>
        <a href="https://assets.publishing.service.gov.uk/media/old/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Dec_2025.csv">Older</a>
        <a href="https://assets.publishing.service.gov.uk/media/abc123/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv">Latest</a>
      </body>
    </html>
    """

    resolved = extract_latest_ofsted_asset_url(html_payload)

    assert resolved.startswith("https://assets.publishing.service.gov.uk/media/")
    assert resolved.endswith("_latest_inspections_as_at_31_Jan_2026.csv")


def test_normalize_ofsted_row_returns_typed_record_for_graded_value() -> None:
    normalized, rejection = normalize_ofsted_latest_row(
        _row(),
        source_asset_url="https://assets.publishing.service.gov.uk/media/abc/latest.csv",
        source_asset_month="2026-01",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.urn == "100001"
    assert normalized.inspection_start_date == date(2026, 1, 15)
    assert normalized.publication_date == date(2026, 2, 20)
    assert normalized.overall_effectiveness_code == "2"
    assert normalized.overall_effectiveness_label == "Good"
    assert normalized.latest_oeif_inspection_start_date == date(2026, 1, 15)
    assert normalized.latest_oeif_publication_date == date(2026, 2, 20)
    assert normalized.quality_of_education_code == "2"
    assert normalized.quality_of_education_label == "Good"
    assert normalized.behaviour_and_attitudes_code == "2"
    assert normalized.behaviour_and_attitudes_label == "Good"
    assert normalized.personal_development_code == "2"
    assert normalized.personal_development_label == "Good"
    assert normalized.leadership_and_management_code == "2"
    assert normalized.leadership_and_management_label == "Good"
    assert normalized.latest_ungraded_inspection_date is None
    assert normalized.latest_ungraded_publication_date is None
    assert normalized.is_graded is True
    assert normalized.ungraded_outcome is None
    assert (
        normalized.provider_page_url
        == "https://reports.ofsted.gov.uk/inspection-reports/find-inspection-report/provider/ELS/100001"
    )


def test_normalize_ofsted_row_keeps_reports_host_when_already_present() -> None:
    normalized, rejection = normalize_ofsted_latest_row(
        _row(
            **{"Web Link (opens in new window)": "https://reports.ofsted.gov.uk/provider/21/100001"}
        ),
        source_asset_url="https://assets.publishing.service.gov.uk/media/abc/latest.csv",
        source_asset_month="2026-01",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.provider_page_url == "https://reports.ofsted.gov.uk/provider/21/100001"


def test_normalize_ofsted_row_supports_ungraded_outcome_when_code_missing() -> None:
    normalized, rejection = normalize_ofsted_latest_row(
        _row(
            **{
                "Latest OEIF overall effectiveness": "",
                "Ungraded inspection overall outcome": "Maintained standards",
            }
        ),
        source_asset_url="https://assets.publishing.service.gov.uk/media/abc/latest.csv",
        source_asset_month="2026-01",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.overall_effectiveness_code is None
    assert normalized.overall_effectiveness_label is None
    assert normalized.is_graded is False
    assert normalized.ungraded_outcome == "Maintained standards"


def test_normalize_ofsted_row_rejects_missing_provider_page_url() -> None:
    normalized, rejection = normalize_ofsted_latest_row(
        _row(**{"Web Link (opens in new window)": ""}),
        source_asset_url="https://assets.publishing.service.gov.uk/media/abc/latest.csv",
        source_asset_month="2026-01",
    )

    assert normalized is None
    assert rejection == "missing_provider_page_url"


def test_normalize_ofsted_row_treats_null_code_as_missing() -> None:
    normalized, rejection = normalize_ofsted_latest_row(
        _row(**{"Latest OEIF overall effectiveness": "NULL"}),
        source_asset_url="https://assets.publishing.service.gov.uk/media/abc/latest.csv",
        source_asset_month="2026-01",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.overall_effectiveness_code is None
    assert normalized.overall_effectiveness_label is None
    assert normalized.is_graded is False


def test_normalize_ofsted_row_maps_code_9_to_not_judged() -> None:
    normalized, rejection = normalize_ofsted_latest_row(
        _row(**{"Latest OEIF overall effectiveness": "9"}),
        source_asset_url="https://assets.publishing.service.gov.uk/media/abc/latest.csv",
        source_asset_month="2026-01",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.overall_effectiveness_code == "Not judged"
    assert normalized.overall_effectiveness_label == "Not judged"
    assert normalized.is_graded is False


def test_normalize_ofsted_row_rejects_missing_urn() -> None:
    normalized, rejection = normalize_ofsted_latest_row(
        _row(URN=""),
        source_asset_url="https://assets.publishing.service.gov.uk/media/abc/latest.csv",
        source_asset_month="2026-01",
    )

    assert normalized is None
    assert rejection == "missing_urn"


def test_normalize_ofsted_row_rejects_invalid_date() -> None:
    normalized, rejection = normalize_ofsted_latest_row(
        _row(**{"Inspection start date": "not-a-date"}),
        source_asset_url="https://assets.publishing.service.gov.uk/media/abc/latest.csv",
        source_asset_month="2026-01",
    )

    assert normalized is None
    assert rejection == "invalid_inspection_start_date"


def test_normalize_ofsted_row_rejects_unknown_effectiveness_value() -> None:
    normalized, rejection = normalize_ofsted_latest_row(
        _row(**{"Latest OEIF overall effectiveness": "5"}),
        source_asset_url="https://assets.publishing.service.gov.uk/media/abc/latest.csv",
        source_asset_month="2026-01",
    )

    assert normalized is None
    assert rejection == "invalid_overall_effectiveness_code"


def test_normalize_ofsted_row_rejects_unknown_sub_judgement_value() -> None:
    normalized, rejection = normalize_ofsted_latest_row(
        _row(**{"Latest OEIF quality of education": "5"}),
        source_asset_url="https://assets.publishing.service.gov.uk/media/abc/latest.csv",
        source_asset_month="2026-01",
    )

    assert normalized is None
    assert rejection == "invalid_quality_of_education_code"


def test_ofsted_fixture_is_present() -> None:
    assert (FIXTURES_DIR / "latest_inspections_valid.csv").exists()
    assert (FIXTURES_DIR / "latest_inspections_mixed.csv").exists()
