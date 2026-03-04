from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SCRIPT_PATH = (
    Path(__file__).resolve().parents[4] / "tools" / "scripts" / "verify_phase_s_sources.py"
)


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_phase_s_sources", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load script module from {SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _build_release_html(*, release_version_id: str, file_id: str, file_name: str) -> str:
    return f"""
    <html>
      <script id="__NEXT_DATA__" type="application/json">{{
        "props": {{
          "pageProps": {{
            "releaseVersion": {{
              "id": "{release_version_id}",
              "downloadFiles": [
                {{"id": "{file_id}", "name": "{file_name}"}}
              ]
            }}
          }}
        }}
      }}</script>
    </html>
    """


def test_verify_phase_s_sources_passes_for_valid_catalog() -> None:
    module = _load_script_module()

    spc_release = _build_release_html(
        release_version_id="spc-rv-2024",
        file_id="spc-file-2024",
        file_name="School level underlying data 2025",
    )
    sen_release = _build_release_html(
        release_version_id="sen-rv-2024",
        file_id="sen-file-2024",
        file_name="School level underlying data 2025",
    )

    urls = {
        module.build_release_page_url(
            publication_slug="school-pupils-and-their-characteristics",
            release_slug="2024-25",
        ): module.HttpResponse(status_code=200, body=spc_release),
        module.build_release_page_url(
            publication_slug="special-educational-needs-in-england",
            release_slug="2024-25",
        ): module.HttpResponse(status_code=200, body=sen_release),
        "https://content.explore-education-statistics.service.gov.uk/api/releases/spc-rv-2024/files/spc-file-2024": module.HttpResponse(
            status_code=200,
            body=(
                "urn,% of pupils known to be eligible for free school meals,"
                "% of pupils known to be eligible for free school meals (Performance Tables),"
                "% of pupils whose first language is known or believed to be other than English,"
                "% of pupils whose first language is known or believed to be English,"
                "% of pupils whose first language is unclassified\n"
                "100001,18.1,18.2,7.1,91.8,1.1\n"
            ),
        ),
        "https://content.explore-education-statistics.service.gov.uk/api/releases/sen-rv-2024/files/sen-file-2024": module.HttpResponse(
            status_code=200,
            body=("URN,time_period,Total pupils,SEN support,EHC plan\n100001,202425,240,34,10\n"),
        ),
    }

    def fetcher(url: str) -> object:
        if url not in urls:
            raise AssertionError(f"Unexpected URL: {url}")
        return urls[url]

    outcome = module.verify_phase_s_sources(
        spc_publication_slug="school-pupils-and-their-characteristics",
        sen_publication_slug="special-educational-needs-in-england",
        release_slugs=("2024-25",),
        lookback_years=1,
        fetcher=fetcher,
    )

    assert outcome.ok
    assert outcome.issues == ()
    assert len(outcome.catalog_entries) == 2


def test_verify_phase_s_sources_fails_when_required_columns_are_missing() -> None:
    module = _load_script_module()

    spc_release = _build_release_html(
        release_version_id="spc-rv-2024",
        file_id="spc-file-2024",
        file_name="School level underlying data 2025",
    )
    sen_release = _build_release_html(
        release_version_id="sen-rv-2024",
        file_id="sen-file-2024",
        file_name="School level underlying data 2025",
    )

    urls = {
        module.build_release_page_url(
            publication_slug="school-pupils-and-their-characteristics",
            release_slug="2024-25",
        ): module.HttpResponse(status_code=200, body=spc_release),
        module.build_release_page_url(
            publication_slug="special-educational-needs-in-england",
            release_slug="2024-25",
        ): module.HttpResponse(status_code=200, body=sen_release),
        "https://content.explore-education-statistics.service.gov.uk/api/releases/spc-rv-2024/files/spc-file-2024": module.HttpResponse(
            status_code=200,
            body=(
                "urn,% of pupils known to be eligible for free school meals (Performance Tables),"
                "% of pupils whose first language is known or believed to be other than English\n"
                "100001,18.2,7.1\n"
            ),
        ),
        "https://content.explore-education-statistics.service.gov.uk/api/releases/sen-rv-2024/files/sen-file-2024": module.HttpResponse(
            status_code=200,
            body=("URN,time_period,Total pupils,SEN support\n100001,202425,240,34\n"),
        ),
    }

    def fetcher(url: str) -> object:
        if url not in urls:
            raise AssertionError(f"Unexpected URL: {url}")
        return urls[url]

    outcome = module.verify_phase_s_sources(
        spc_publication_slug="school-pupils-and-their-characteristics",
        sen_publication_slug="special-educational-needs-in-england",
        release_slugs=("2024-25",),
        lookback_years=1,
        fetcher=fetcher,
    )

    assert not outcome.ok
    assert any("missing required columns" in issue for issue in outcome.issues)


def test_parse_csv_headers_rejects_empty_payload() -> None:
    module = _load_script_module()

    try:
        module.parse_csv_headers("")
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty CSV payload")
