from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from civitas.infrastructure.pipelines.base import PipelineRunContext, PipelineSource
from civitas.infrastructure.pipelines.demographics_release_files import (
    BRONZE_MANIFEST_FILE_NAME,
    DemographicsReleaseFilesPipeline,
)


def _context(bronze_root: Path) -> PipelineRunContext:
    return PipelineRunContext(
        run_id=uuid4(),
        source=PipelineSource.DFE_CHARACTERISTICS,
        started_at=datetime(2026, 3, 4, 12, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def _release_html(*, release_version_id: str, file_id: str, file_name: str) -> str:
    return (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(
            {
                "props": {
                    "pageProps": {
                        "releaseVersion": {
                            "id": release_version_id,
                            "downloadFiles": [{"id": file_id, "name": file_name}],
                        }
                    }
                }
            }
        )
        + "</script></html>"
    )


def test_demographics_release_files_download_writes_manifest_and_is_idempotent(
    tmp_path: Path,
) -> None:
    spc_page = _release_html(
        release_version_id="spc-rv-2024",
        file_id="spc-file-2024",
        file_name="School level underlying data 2025",
    )
    sen_page = _release_html(
        release_version_id="sen-rv-2024",
        file_id="sen-file-2024",
        file_name="School level underlying data 2025",
    )

    urls = {
        "https://explore-education-statistics.service.gov.uk/find-statistics/school-pupils-and-their-characteristics/2024-25": spc_page,
        "https://explore-education-statistics.service.gov.uk/find-statistics/special-educational-needs-in-england/2024-25": sen_page,
        "https://content.explore-education-statistics.service.gov.uk/api/releases/spc-rv-2024/files/spc-file-2024": (
            "urn,time_period,% of pupils known to be eligible for free school meals (Performance Tables),"
            "% of pupils whose first language is known or believed to be other than English,"
            "% of pupils whose first language is known or believed to be English,"
            "% of pupils whose first language is unclassified\n"
            "100001,202425,18.4,11.2,87.9,0.9\n"
        ),
        "https://content.explore-education-statistics.service.gov.uk/api/releases/sen-rv-2024/files/sen-file-2024": (
            "URN,time_period,Total pupils,SEN support,EHC plan\n100001,202425,250,37,11\n"
        ),
    }

    def fetcher(url: str) -> str:
        if url not in urls:
            raise AssertionError(f"Unexpected URL: {url}")
        return urls[url]

    pipeline = DemographicsReleaseFilesPipeline(
        engine=None,
        spc_publication_slug="school-pupils-and-their-characteristics",
        sen_publication_slug="special-educational-needs-in-england",
        release_slugs=("2024-25",),
        lookback_years=1,
        strict_mode=True,
        fetcher=fetcher,
    )
    context = _context(tmp_path / "bronze")

    first_downloaded = pipeline.download(context)
    second_downloaded = pipeline.download(context)

    assert first_downloaded == 2
    assert second_downloaded == 2

    manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["normalization_contract_version"] == "demographics_release_files.v1"
    assert payload["lookback_years"] == 1
    assert len(payload["assets"]) == 2
    assert payload["assets"][0]["row_count"] == 1
    assert payload["assets"][1]["row_count"] == 1
