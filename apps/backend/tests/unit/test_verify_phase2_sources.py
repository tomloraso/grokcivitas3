from __future__ import annotations

import gzip
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable

SCRIPT_PATH = Path(__file__).resolve().parents[4] / "tools" / "scripts" / "verify_phase2_sources.py"


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_phase2_sources", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        msg = f"Unable to load script module from {SCRIPT_PATH}"
        raise RuntimeError(msg)

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _build_fetcher(
    module: ModuleType,
    responses: dict[str, tuple[int, str]],
) -> Callable[[str], object]:
    def _fetch(url: str) -> object:
        if url not in responses:
            msg = f"Unexpected URL: {url}"
            raise AssertionError(msg)
        status_code, text = responses[url]
        return module.HttpResponse(status_code=status_code, body=text)

    return _fetch


def test_extract_ofsted_timeline_asset_urls_prefers_latest_dates() -> None:
    module = _load_script_module()

    html = """
    <html>
      <body>
        <a href="https://assets.publishing.service.gov.uk/media/old/Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_30_Nov_2025.csv">old-all</a>
        <a href="https://assets.publishing.service.gov.uk/media/new/Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_31_Jan_2026.csv">new-all</a>
        <a href="https://assets.publishing.service.gov.uk/media/old2/Management_information_-_state-funded_schools_-_latest_inspections_as_at_30_Nov_2025.csv">old-latest</a>
        <a href="https://assets.publishing.service.gov.uk/media/new2/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv">new-latest</a>
        <a href="https://assets.publishing.service.gov.uk/media/historical/Management_information_-_state-funded_schools_1_September_2015_to_31_August_2019.csv">historical</a>
      </body>
    </html>
    """

    all_inspections, latest_inspections, historical = module.extract_ofsted_timeline_asset_urls(
        html
    )

    assert all_inspections.endswith("published_by_31_Jan_2026.csv")
    assert latest_inspections.endswith("as_at_31_Jan_2026.csv")
    assert historical.endswith("1_September_2015_to_31_August_2019.csv")


def test_parse_csv_headers_supports_preamble_skip() -> None:
    module = _load_script_module()

    headers = module.parse_csv_headers(
        "Metadata preamble line\nAcademic year,URN,Inspection number\n2025/26,100001,ABC123",
        skip_rows=1,
    )

    assert headers == ["Academic year", "URN", "Inspection number"]


def test_extract_latest_police_archive_url_prefers_latest_month() -> None:
    module = _load_script_module()

    html = """
    <html>
      <a href="/data/archive/2025-12.zip">2025-12</a>
      <a href="/data/archive/2026-01.zip">2026-01</a>
    </html>
    """

    archive_url = module.extract_latest_police_archive_url(html)
    assert archive_url == "https://data.police.uk/data/archive/2026-01.zip"


def test_decode_response_bytes_handles_gzip_payloads() -> None:
    module = _load_script_module()

    payload = "URN,Inspection start date\n100001,2026-01-01".encode("utf-8")
    decoded = module._decode_response_bytes(gzip.compress(payload), None)

    assert decoded.startswith("URN,Inspection start date")


def test_verify_phase2_sources_passes_when_contract_checks_succeed() -> None:
    module = _load_script_module()

    ofsted_landing_html = """
    <html>
      <a href="https://assets.publishing.service.gov.uk/media/new/Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_31_Jan_2026.csv">all</a>
      <a href="https://assets.publishing.service.gov.uk/media/latest/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv">latest</a>
      <a href="https://assets.publishing.service.gov.uk/media/historical/Management_information_-_state-funded_schools_1_September_2015_to_31_August_2019.csv">historical</a>
    </html>
    """

    responses = {
        module.OFSTED_LANDING_PAGE_URL: (200, ofsted_landing_html),
        "https://assets.publishing.service.gov.uk/media/new/Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_31_Jan_2026.csv": (
            200,
            ",".join(module.REQUIRED_OFSTED_ALL_INSPECTIONS_HEADERS)
            + "\n100001,ABC123,S5 Inspection,2026-01-11,2026-01-20",
        ),
        "https://assets.publishing.service.gov.uk/media/latest/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv": (
            200,
            ",".join(module.REQUIRED_OFSTED_LATEST_HEADERS) + "\n100001,2026-01-11,2026-01-20,2,",
        ),
        "https://assets.publishing.service.gov.uk/media/historical/Management_information_-_state-funded_schools_1_September_2015_to_31_August_2019.csv": (
            200,
            "Metadata preamble line\n"
            + ",".join(module.REQUIRED_OFSTED_HISTORICAL_HEADERS)
            + "\n2025/26,100001,ABC122,2019-07-18,2019-08-01,2",
        ),
        module.IMD_2025_LANDING_PAGE_URL: (200, "<html>IoD2025</html>"),
        module.IMD_2025_FILE_7_URL: (
            200,
            ",".join(module.REQUIRED_IMD_2025_HEADERS) + "\nE01000001,LSOA A,3,0.21,2",
        ),
        module.IMD_2019_LANDING_PAGE_URL: (200, "<html>IoD2019</html>"),
        module.IMD_2019_FILE_7_URL: (
            200,
            ",".join(module.REQUIRED_IMD_2019_HEADERS) + "\nE01000001,3,0.21,2",
        ),
        module.POLICE_ARCHIVE_INDEX_URL: (
            200,
            "<html><a href='/data/archive/2025-12.zip'>2025-12</a><a href='/data/archive/2026-01.zip'>2026-01</a></html>",
        ),
        "https://data.police.uk/data/archive/2026-01.zip": (200, "zip-bytes-placeholder"),
        module.POLICE_COLUMNS_REFERENCE_URL: (
            200,
            "Longitude Latitude LSOA code Crime type",
        ),
        module.POLICE_LAST_UPDATED_URL: (200, '{"date":"2026-01-01"}'),
        module.POLICE_STREET_DATES_URL: (200, '[{"date":"2025-12"},{"date":"2026-01"}]'),
        module.POLICE_CRIME_CATEGORIES_URL_TEMPLATE.format(month="2026-01"): (
            200,
            '[{"url":"violent-crime","name":"Violence and sexual offences"}]',
        ),
        module.POLICE_ALL_CRIME_URL_TEMPLATE.format(
            lat="51.5072", lng="-0.1276", month="2026-01"
        ): (
            200,
            (
                '[{"category":"violent-crime","location":{"latitude":"51.50","longitude":"-0.12"},'
                '"month":"2026-01"}]'
            ),
        ),
        module.POLICE_API_LIMITS_URL: (200, "15 requests per second ... 429"),
        module.POSTCODES_IO_URL_TEMPLATE.format(postcode="SW1A2AA"): (
            200,
            '{"result":{"codes":{"lsoa":"E01004736"},"lsoa":"Westminster 018C","latitude":51.5035,"longitude":-0.1276}}',
        ),
    }
    fetcher = _build_fetcher(module, responses)

    outcome = module.verify_phase2_sources(fetcher=fetcher)

    assert outcome.ok
    assert outcome.issues == []


def test_verify_phase2_sources_fails_when_required_headers_are_missing() -> None:
    module = _load_script_module()

    ofsted_landing_html = """
    <html>
      <a href="https://assets.publishing.service.gov.uk/media/new/Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_31_Jan_2026.csv">all</a>
      <a href="https://assets.publishing.service.gov.uk/media/latest/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv">latest</a>
      <a href="https://assets.publishing.service.gov.uk/media/historical/Management_information_-_state-funded_schools_1_September_2015_to_31_August_2019.csv">historical</a>
    </html>
    """

    responses = {
        module.OFSTED_LANDING_PAGE_URL: (200, ofsted_landing_html),
        "https://assets.publishing.service.gov.uk/media/new/Management_information_-_state-funded_schools_-_all_inspections_-_year_to_date_published_by_31_Jan_2026.csv": (
            200,
            ",".join(module.REQUIRED_OFSTED_ALL_INSPECTIONS_HEADERS)
            + "\n100001,ABC123,S5 Inspection,2026-01-11,2026-01-20",
        ),
        "https://assets.publishing.service.gov.uk/media/latest/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv": (
            200,
            ",".join(module.REQUIRED_OFSTED_LATEST_HEADERS) + "\n100001,2026-01-11,2026-01-20,2,",
        ),
        "https://assets.publishing.service.gov.uk/media/historical/Management_information_-_state-funded_schools_1_September_2015_to_31_August_2019.csv": (
            200,
            "Metadata preamble line\n"
            + ",".join(module.REQUIRED_OFSTED_HISTORICAL_HEADERS)
            + "\n2025/26,100001,ABC122,2019-07-18,2019-08-01,2",
        ),
        module.IMD_2025_LANDING_PAGE_URL: (200, "<html>IoD2025</html>"),
        module.IMD_2025_FILE_7_URL: (
            200,
            "LSOA code (2021),LSOA name (2021)\nE01000001,LSOA A",
        ),
        module.IMD_2019_LANDING_PAGE_URL: (200, "<html>IoD2019</html>"),
        module.IMD_2019_FILE_7_URL: (
            200,
            ",".join(module.REQUIRED_IMD_2019_HEADERS) + "\nE01000001,3,0.21,2",
        ),
        module.POLICE_ARCHIVE_INDEX_URL: (
            200,
            "<html><a href='/data/archive/2026-01.zip'>2026-01</a></html>",
        ),
        "https://data.police.uk/data/archive/2026-01.zip": (200, "zip-bytes-placeholder"),
        module.POLICE_COLUMNS_REFERENCE_URL: (
            200,
            "Longitude Latitude LSOA code Crime type",
        ),
        module.POLICE_LAST_UPDATED_URL: (200, '{"date":"2026-01-01"}'),
        module.POLICE_STREET_DATES_URL: (200, '[{"date":"2026-01"}]'),
        module.POLICE_CRIME_CATEGORIES_URL_TEMPLATE.format(month="2026-01"): (
            200,
            '[{"url":"violent-crime","name":"Violence and sexual offences"}]',
        ),
        module.POLICE_ALL_CRIME_URL_TEMPLATE.format(
            lat="51.5072", lng="-0.1276", month="2026-01"
        ): (
            200,
            (
                '[{"category":"violent-crime","location":{"latitude":"51.50","longitude":"-0.12"},'
                '"month":"2026-01"}]'
            ),
        ),
        module.POLICE_API_LIMITS_URL: (200, "15 requests per second ... 429"),
        module.POSTCODES_IO_URL_TEMPLATE.format(postcode="SW1A2AA"): (
            200,
            '{"result":{"codes":{"lsoa":"E01004736"},"lsoa":"Westminster 018C","latitude":51.5035,"longitude":-0.1276}}',
        ),
    }
    fetcher = _build_fetcher(module, responses)

    outcome = module.verify_phase2_sources(fetcher=fetcher)

    assert not outcome.ok
    assert any("Missing IoD2025 CSV header(s)" in issue for issue in outcome.issues)
