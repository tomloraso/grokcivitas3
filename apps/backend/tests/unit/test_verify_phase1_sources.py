from __future__ import annotations

import gzip
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable

SCRIPT_PATH = Path(__file__).resolve().parents[4] / "tools" / "scripts" / "verify_phase1_sources.py"


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_phase1_sources", SCRIPT_PATH)
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


def test_extract_latest_ofsted_asset_url_prefers_latest_inspections_csv() -> None:
    module = _load_script_module()

    html = """
    <html>
      <body>
        <a href="https://assets.publishing.service.gov.uk/media/aaa/Management_information_-_state-funded_schools_-_latest_inspections_at_30_Nov_2019.csv">old</a>
        <a href="https://assets.publishing.service.gov.uk/media/def/Management_information_-_state-funded_schools_-_latest_inspections_as_at_31_Jan_2026.csv">latest</a>
      </body>
    </html>
    """

    url = module.extract_latest_ofsted_asset_url(html)
    assert url.endswith("latest_inspections_as_at_31_Jan_2026.csv")


def test_parse_csv_headers_handles_utf8_bom() -> None:
    module = _load_script_module()

    headers = module.parse_csv_headers(
        "\ufeffURN,Inspection start date,Publication date\n1,2026-01-01,2026-01-10"
    )

    assert headers == ["URN", "Inspection start date", "Publication date"]


def test_decode_response_bytes_handles_gzip_payloads() -> None:
    module = _load_script_module()

    payload = "school_urn,time_period\n100001,2024/25".encode("utf-8")
    decoded = module._decode_response_bytes(gzip.compress(payload), None)

    assert decoded.startswith("school_urn,time_period")


def test_verify_phase1_sources_passes_when_contract_checks_succeed() -> None:
    module = _load_script_module()

    responses = {
        module.DFE_PUBLICATIONS_URL: (
            200,
            '{"results":[{"id":"pub-1","title":"Key stage 2 attainment"}]}',
        ),
        module.DFE_DATASETS_URL_TEMPLATE.format(publication_id="pub-1"): (200, '{"results":[]}'),
        module.DFE_DATASET_URL_TEMPLATE.format(dataset_id=module.DEFAULT_DFE_DATASET_ID): (
            200,
            "{}",
        ),
        module.DFE_DATASET_META_URL_TEMPLATE.format(dataset_id=module.DEFAULT_DFE_DATASET_ID): (
            200,
            "{}",
        ),
        module.DFE_DATASET_QUERY_URL_TEMPLATE.format(dataset_id=module.DEFAULT_DFE_DATASET_ID): (
            200,
            '{"results":[{"school_urn":"100001"}]}',
        ),
        module.DFE_DATASET_CSV_URL_TEMPLATE.format(dataset_id=module.DEFAULT_DFE_DATASET_ID): (
            200,
            ",".join(module.REQUIRED_DFE_CSV_HEADERS) + "\n100001,2024/25,1,2,3,4,5,6,7",
        ),
        module.OFSTED_LANDING_PAGE_URL: (
            200,
            """
            <html>
              <a href="https://assets.publishing.service.gov.uk/media/698/latest_inspections_as_at_31_Jan_2026.csv">latest</a>
            </html>
            """,
        ),
        "https://assets.publishing.service.gov.uk/media/698/latest_inspections_as_at_31_Jan_2026.csv": (
            200,
            ",".join(module.REQUIRED_OFSTED_CSV_HEADERS) + "\n100001,2026-01-01,2026-01-10,2,",
        ),
    }
    fetcher = _build_fetcher(module, responses)

    outcome = module.verify_phase1_sources(fetcher=fetcher)

    assert outcome.ok
    assert outcome.issues == []


def test_verify_phase1_sources_fails_when_required_headers_are_missing() -> None:
    module = _load_script_module()

    responses = {
        module.DFE_PUBLICATIONS_URL: (
            200,
            '{"results":[{"id":"pub-1","title":"Key stage 2 attainment"}]}',
        ),
        module.DFE_DATASETS_URL_TEMPLATE.format(publication_id="pub-1"): (200, '{"results":[]}'),
        module.DFE_DATASET_URL_TEMPLATE.format(dataset_id=module.DEFAULT_DFE_DATASET_ID): (
            200,
            "{}",
        ),
        module.DFE_DATASET_META_URL_TEMPLATE.format(dataset_id=module.DEFAULT_DFE_DATASET_ID): (
            200,
            "{}",
        ),
        module.DFE_DATASET_QUERY_URL_TEMPLATE.format(dataset_id=module.DEFAULT_DFE_DATASET_ID): (
            200,
            '{"results":[{"school_urn":"100001"}]}',
        ),
        module.DFE_DATASET_CSV_URL_TEMPLATE.format(dataset_id=module.DEFAULT_DFE_DATASET_ID): (
            200,
            "school_urn,time_period\n100001,2024/25",
        ),
        module.OFSTED_LANDING_PAGE_URL: (
            200,
            """
            <html>
              <a href="https://assets.publishing.service.gov.uk/media/698/latest_inspections_as_at_31_Jan_2026.csv">latest</a>
            </html>
            """,
        ),
        "https://assets.publishing.service.gov.uk/media/698/latest_inspections_as_at_31_Jan_2026.csv": (
            200,
            ",".join(module.REQUIRED_OFSTED_CSV_HEADERS) + "\n100001,2026-01-01,2026-01-10,2,",
        ),
    }
    fetcher = _build_fetcher(module, responses)

    outcome = module.verify_phase1_sources(fetcher=fetcher)

    assert not outcome.ok
    assert any("Missing DfE CSV header(s)" in issue for issue in outcome.issues)
