from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from civitas.infrastructure.pipelines.base import PipelineRunContext, PipelineSource
from civitas.infrastructure.pipelines.contracts import (
    dfe_attendance as attendance_contract,
)
from civitas.infrastructure.pipelines.contracts import (
    dfe_behaviour as behaviour_contract,
)
from civitas.infrastructure.pipelines.contracts import (
    dfe_performance as performance_contract,
)
from civitas.infrastructure.pipelines.contracts import (
    dfe_workforce as workforce_contract,
)
from civitas.infrastructure.pipelines.contracts import (
    gias as gias_contract,
)
from civitas.infrastructure.pipelines.contracts import (
    ofsted_latest as ofsted_latest_contract,
)
from civitas.infrastructure.pipelines.contracts import (
    ofsted_timeline as ofsted_timeline_contract,
)
from civitas.infrastructure.pipelines.contracts import (
    ons_imd as ons_imd_contract,
)
from civitas.infrastructure.pipelines.contracts import (
    police as police_contract,
)
from civitas.infrastructure.pipelines.demographics_release_files import (
    BRONZE_MANIFEST_FILE_NAME as DEMOGRAPHICS_MANIFEST_FILE_NAME,
)
from civitas.infrastructure.pipelines.demographics_release_files import (
    DemographicsReleaseFilesPipeline,
)
from civitas.infrastructure.pipelines.dfe_attendance import (
    BRONZE_MANIFEST_FILE_NAME as DFE_ATTENDANCE_MANIFEST_FILE_NAME,
)
from civitas.infrastructure.pipelines.dfe_attendance import (
    DfeAttendancePipeline,
)
from civitas.infrastructure.pipelines.dfe_behaviour import (
    BRONZE_MANIFEST_FILE_NAME as DFE_BEHAVIOUR_MANIFEST_FILE_NAME,
)
from civitas.infrastructure.pipelines.dfe_behaviour import (
    DfeBehaviourPipeline,
)
from civitas.infrastructure.pipelines.dfe_performance import (
    BRONZE_MANIFEST_FILE_NAME as DFE_PERFORMANCE_MANIFEST_FILE_NAME,
)
from civitas.infrastructure.pipelines.dfe_performance import (
    DfePerformancePipeline,
)
from civitas.infrastructure.pipelines.dfe_workforce import (
    BRONZE_MANIFEST_FILE_NAME as DFE_WORKFORCE_MANIFEST_FILE_NAME,
)
from civitas.infrastructure.pipelines.dfe_workforce import (
    DfeWorkforcePipeline,
)
from civitas.infrastructure.pipelines.gias import (
    BRONZE_FILE_NAME as GIAS_BRONZE_FILE_NAME,
)
from civitas.infrastructure.pipelines.gias import (
    GiasPipeline,
)
from civitas.infrastructure.pipelines.ofsted_latest import (
    BRONZE_FILE_NAME as OFSTED_LATEST_BRONZE_FILE_NAME,
)
from civitas.infrastructure.pipelines.ofsted_latest import (
    OfstedLatestPipeline,
)
from civitas.infrastructure.pipelines.ofsted_timeline import (
    BRONZE_MANIFEST_FILE_NAME,
    OfstedTimelinePipeline,
)
from civitas.infrastructure.pipelines.ons_imd import (
    BRONZE_METADATA_FILE_NAME as ONS_METADATA_FILE_NAME,
)
from civitas.infrastructure.pipelines.ons_imd import (
    OnsImdPipeline,
)
from civitas.infrastructure.pipelines.police_crime_context import (
    BRONZE_METADATA_FILE_NAME as POLICE_METADATA_FILE_NAME,
)
from civitas.infrastructure.pipelines.police_crime_context import (
    PoliceCrimeContextPipeline,
)

FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures"


def _context(source: PipelineSource, bronze_root: Path) -> PipelineRunContext:
    return PipelineRunContext(
        run_id=uuid4(),
        source=source,
        started_at=datetime(2026, 3, 3, 10, 0, tzinfo=timezone.utc),
        bronze_root=bronze_root,
    )


def test_gias_download_writes_contract_version_to_metadata(tmp_path: Path) -> None:
    fixture = FIXTURES_ROOT / "gias" / "edubasealldata_valid.csv"
    pipeline = GiasPipeline(engine=None, source_csv=str(fixture))
    context = _context(PipelineSource.GIAS, tmp_path / "bronze")

    pipeline.download(context)

    metadata_path = context.bronze_source_path / GIAS_BRONZE_FILE_NAME
    payload = json.loads(metadata_path.with_suffix(".metadata.json").read_text(encoding="utf-8"))
    assert payload["normalization_contract_version"] == gias_contract.CONTRACT_VERSION


def test_demographics_download_writes_contract_version_to_manifest(tmp_path: Path) -> None:
    spc_release_html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"releaseVersion":{"id":"spc-rv-1","downloadFiles":[{"id":"spc-file-1","name":"School level underlying data 2025"}]}}}}'
        "</script></html>"
    )
    sen_release_html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"releaseVersion":{"id":"sen-rv-1","downloadFiles":[{"id":"sen-file-1","name":"School level underlying data 2025"}]}}}}'
        "</script></html>"
    )
    spc_csv = (
        "urn,time_period,% of pupils known to be eligible for free school meals (Performance Tables),"
        "% of pupils whose first language is known or believed to be other than English,"
        "% of pupils whose first language is known or believed to be English,"
        "% of pupils whose first language is unclassified\n"
        "100001,202425,18.2,8.4,90.6,1.0\n"
    )
    sen_csv = "URN,time_period,Total pupils,SEN support,EHC plan\n100001,202425,240,36,9\n"
    responses = {
        "https://explore-education-statistics.service.gov.uk/find-statistics/school-pupils-and-their-characteristics/2024-25": spc_release_html,
        "https://explore-education-statistics.service.gov.uk/find-statistics/special-educational-needs-in-england/2024-25": sen_release_html,
        "https://content.explore-education-statistics.service.gov.uk/api/releases/spc-rv-1/files/spc-file-1": spc_csv,
        "https://content.explore-education-statistics.service.gov.uk/api/releases/sen-rv-1/files/sen-file-1": sen_csv,
    }

    def fetcher(url: str) -> str:
        if url not in responses:
            raise AssertionError(f"Unexpected URL: {url}")
        return responses[url]

    pipeline = DemographicsReleaseFilesPipeline(
        engine=None,
        spc_publication_slug="school-pupils-and-their-characteristics",
        sen_publication_slug="special-educational-needs-in-england",
        release_slugs=("2024-25",),
        lookback_years=1,
        fetcher=fetcher,
    )
    context = _context(PipelineSource.DFE_CHARACTERISTICS, tmp_path / "bronze")

    pipeline.download(context)

    manifest_path = context.bronze_source_path / DEMOGRAPHICS_MANIFEST_FILE_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["normalization_contract_version"] == "demographics_release_files.v1"
    assert len(payload["assets"]) == 2


def test_dfe_performance_download_writes_contract_version_to_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    ks2_dataset_id = "ks2-dataset"
    ks4_dataset_id = "ks4-dataset"

    def fake_download_json(url: str, *, timeout_seconds: float) -> dict[str, object]:
        parsed_url = urlsplit(url)
        query = parse_qs(parsed_url.query)
        if parsed_url.path.endswith(f"/data-sets/{ks2_dataset_id}/meta"):
            assert query.get("dataSetVersion") == ["ks2-v1"]
            return {
                "locations": {
                    "options": [
                        {"id": "100001", "code": "100001"},
                    ]
                }
            }
        if parsed_url.path.endswith(f"/data-sets/{ks4_dataset_id}/meta"):
            assert query.get("dataSetVersion") == ["ks4-v1"]
            return {
                "locations": {
                    "options": [
                        {"id": "100001", "code": "100001"},
                    ]
                }
            }
        if parsed_url.path.endswith(f"/data-sets/{ks2_dataset_id}"):
            assert query == {}
            return {"latestVersion": {"version": "ks2-v1"}}
        if parsed_url.path.endswith(f"/data-sets/{ks4_dataset_id}"):
            assert query == {}
            return {"latestVersion": {"version": "ks4-v1"}}
        raise AssertionError(f"Unexpected URL: {url}")

    def fake_post_json(
        url: str,
        *,
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> dict[str, object]:
        parsed_url = urlsplit(url)
        query = parse_qs(parsed_url.query)
        assert payload["page"] == 1
        assert payload["pageSize"] == 10_000
        if parsed_url.path.endswith(f"/data-sets/{ks2_dataset_id}/query"):
            assert query.get("dataSetVersion") == ["ks2-v1"]
            assert payload["indicators"] == list(performance_contract.KS2_INDICATOR_IDS.values())
            return {
                "results": [
                    {
                        "timePeriod": {"period": "2024/2025"},
                        "locations": {"SCH": "100001"},
                        "filters": {"fV8YF": "EXcPq", "jfhAM": "2id7l"},
                        "values": {"IwjBz": "74.0", "i2s6X": "12.0"},
                    }
                ],
                "paging": {"totalPages": 1},
            }
        if parsed_url.path.endswith(f"/data-sets/{ks4_dataset_id}/query"):
            assert query.get("dataSetVersion") == ["ks4-v1"]
            assert payload["indicators"] == list(performance_contract.KS4_INDICATOR_IDS.values())
            return {
                "results": [
                    {
                        "timePeriod": {"period": "2024/2025"},
                        "locations": {"SCH": "100001"},
                        "filters": {
                            "pPmSo": "5Kydi",
                            "IzpBz": "mws9K",
                            "ibG6X": "WCb2b",
                            "LZ6Wj": "9b64v",
                        },
                        "values": {
                            "kgVhs": "47.2",
                            "Pwoeb": "0.11",
                            "dDo0Z": "52.3",
                            "hCRyW": "71.4",
                            "bmztT": "36.2",
                            "uEko4": "25.5",
                            "mqo9K": "31.3",
                        },
                    }
                ],
                "paging": {"totalPages": 1},
            }
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(
        "civitas.infrastructure.pipelines.dfe_performance._download_json",
        fake_download_json,
    )
    monkeypatch.setattr(
        "civitas.infrastructure.pipelines.dfe_performance._post_json",
        fake_post_json,
    )

    pipeline = DfePerformancePipeline(
        engine=None,
        ks2_dataset_id=ks2_dataset_id,
        ks4_dataset_id=ks4_dataset_id,
    )
    context = _context(PipelineSource.DFE_PERFORMANCE, tmp_path / "bronze")

    downloaded_rows = pipeline.download(context)

    manifest_path = context.bronze_source_path / DFE_PERFORMANCE_MANIFEST_FILE_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert downloaded_rows == 2
    assert payload["normalization_contract_version"] == performance_contract.CONTRACT_VERSION
    assert len(payload["datasets"]) == 2
    assert len(payload["assets"]) == 4


def test_dfe_attendance_download_writes_contract_version_to_manifest(tmp_path: Path) -> None:
    release_html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"releaseVersion":{"id":"attendance-rv-1","downloadFiles":[{"id":"attendance-file-1","name":"School level absence data"}]}}}}'
        "</script></html>"
    )
    csv_payload = (
        "school_urn,time_period,geographic_level,sess_overall_percent,enrolments_pa_10_exact_percent\n"
        "100001,202324,School,6.0,14.2\n"
    )
    responses = {
        "https://explore-education-statistics.service.gov.uk/find-statistics/pupil-absence-in-schools-in-england/2023-24": release_html,
        "https://content.explore-education-statistics.service.gov.uk/api/releases/attendance-rv-1/files/attendance-file-1": csv_payload,
    }

    def fetcher(url: str) -> str:
        if url not in responses:
            raise AssertionError(f"Unexpected URL: {url}")
        return responses[url]

    pipeline = DfeAttendancePipeline(
        engine=None,
        publication_slug="pupil-absence-in-schools-in-england",
        release_slugs=("2023-24",),
        lookback_years=1,
        fetcher=fetcher,
    )
    context = _context(PipelineSource.DFE_ATTENDANCE, tmp_path / "bronze")

    pipeline.download(context)

    manifest_path = context.bronze_source_path / DFE_ATTENDANCE_MANIFEST_FILE_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["normalization_contract_version"] == attendance_contract.CONTRACT_VERSION
    assert len(payload["assets"]) == 1


def test_dfe_behaviour_download_writes_contract_version_to_manifest(tmp_path: Path) -> None:
    release_html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"releaseVersion":{"id":"behaviour-rv-1","downloadFiles":[{"id":"behaviour-file-1","name":"School level suspensions and permanent exclusions data"}]}}}}'
        "</script></html>"
    )
    csv_payload = (
        "school_urn,time_period,geographic_level,suspension,susp_rate,perm_excl,perm_excl_rate\n"
        "100001,202324,School,121,16.4,1,0.1\n"
    )
    responses = {
        "https://explore-education-statistics.service.gov.uk/find-statistics/suspensions-and-permanent-exclusions-in-england/2024-25-autumn-term": release_html,
        "https://content.explore-education-statistics.service.gov.uk/api/releases/behaviour-rv-1/files/behaviour-file-1": csv_payload,
    }

    def fetcher(url: str) -> str:
        if url not in responses:
            raise AssertionError(f"Unexpected URL: {url}")
        return responses[url]

    pipeline = DfeBehaviourPipeline(
        engine=None,
        publication_slug="suspensions-and-permanent-exclusions-in-england",
        release_slugs=("2024-25-autumn-term",),
        lookback_years=1,
        fetcher=fetcher,
    )
    context = _context(PipelineSource.DFE_BEHAVIOUR, tmp_path / "bronze")

    pipeline.download(context)

    manifest_path = context.bronze_source_path / DFE_BEHAVIOUR_MANIFEST_FILE_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["normalization_contract_version"] == behaviour_contract.CONTRACT_VERSION
    assert len(payload["assets"]) == 1


def test_dfe_workforce_download_writes_contract_version_to_manifest(tmp_path: Path) -> None:
    release_html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"releaseVersion":{"id":"workforce-rv-1","downloadFiles":[{"id":"workforce-file-1","name":"School level workforce data"}]}}}}'
        "</script></html>"
    )
    csv_payload = (
        "school_urn,time_period,geographic_level,pupil_teacher_ratio,supply_teacher_pct\n"
        "100001,202324,School,16.3,2.4\n"
    )
    responses = {
        "https://explore-education-statistics.service.gov.uk/find-statistics/school-workforce-in-england/2024": release_html,
        "https://content.explore-education-statistics.service.gov.uk/api/releases/workforce-rv-1/files/workforce-file-1": csv_payload,
    }

    def fetcher(url: str) -> str:
        if url not in responses:
            raise AssertionError(f"Unexpected URL: {url}")
        return responses[url]

    pipeline = DfeWorkforcePipeline(
        engine=None,
        publication_slug="school-workforce-in-england",
        release_slugs=("2024",),
        lookback_years=1,
        fetcher=fetcher,
    )
    context = _context(PipelineSource.DFE_WORKFORCE, tmp_path / "bronze")

    pipeline.download(context)

    manifest_path = context.bronze_source_path / DFE_WORKFORCE_MANIFEST_FILE_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["normalization_contract_version"] == workforce_contract.CONTRACT_VERSION
    assert len(payload["assets"]) == 1


def test_ofsted_latest_download_writes_contract_version_to_metadata(tmp_path: Path) -> None:
    fixture = FIXTURES_ROOT / "ofsted_latest" / "latest_inspections_valid.csv"
    pipeline = OfstedLatestPipeline(engine=None, source_csv=str(fixture))
    context = _context(PipelineSource.OFSTED_LATEST, tmp_path / "bronze")

    pipeline.download(context)

    metadata_path = context.bronze_source_path / OFSTED_LATEST_BRONZE_FILE_NAME
    payload = json.loads(metadata_path.with_suffix(".metadata.json").read_text(encoding="utf-8"))
    assert payload["normalization_contract_version"] == ofsted_latest_contract.CONTRACT_VERSION


def test_ofsted_timeline_download_writes_contract_version_to_manifest(tmp_path: Path) -> None:
    fixtures_root = FIXTURES_ROOT / "ofsted_timeline"
    ytd_fixture = fixtures_root / "all_inspections_ytd_mixed.csv"
    historical_fixture = fixtures_root / "all_inspections_historical_2015_2019_mixed.csv"

    pipeline = OfstedTimelinePipeline(
        engine=None,
        source_assets_csv=f"{ytd_fixture},{historical_fixture}",
    )
    context = _context(PipelineSource.OFSTED_TIMELINE, tmp_path / "bronze")

    pipeline.download(context)

    manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["normalization_contract_version"] == ofsted_timeline_contract.CONTRACT_VERSION


def test_ons_download_writes_contract_version_to_metadata(tmp_path: Path) -> None:
    fixture = FIXTURES_ROOT / "ons_imd" / "file_7_valid_2025.csv"
    pipeline = OnsImdPipeline(engine=None, source_csv=str(fixture))
    context = _context(PipelineSource.ONS_IMD, tmp_path / "bronze")

    pipeline.download(context)

    metadata_path = context.bronze_source_path / ONS_METADATA_FILE_NAME
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["normalization_contract_version"] == ons_imd_contract.CONTRACT_VERSION


def test_police_download_writes_contract_version_to_metadata(tmp_path: Path) -> None:
    csv_fixture = FIXTURES_ROOT / "police_crime_context" / "2026-01-example-street.csv"
    archive_path = tmp_path / "crime.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("2026-01-example-street.csv", csv_fixture.read_bytes())

    pipeline = PoliceCrimeContextPipeline(
        engine=None,
        source_archive_url=str(archive_path),
        source_mode="archive",
    )
    context = _context(PipelineSource.POLICE_CRIME_CONTEXT, tmp_path / "bronze")

    pipeline.download(context)

    metadata_path = context.bronze_source_path / POLICE_METADATA_FILE_NAME
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["normalization_contract_version"] == police_contract.CONTRACT_VERSION
    assert payload["archive_months"] == ["2026-01"]
    assert payload["archive_forces"] == ["example"]
    assert payload["archive_month_count"] == 1
    assert payload["archive_force_count"] == 1
