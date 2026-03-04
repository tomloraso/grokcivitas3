from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from civitas.infrastructure.pipelines.base import PipelineRunContext, PipelineSource
from civitas.infrastructure.pipelines.contracts import (
    dfe as dfe_contract,
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
from civitas.infrastructure.pipelines.dfe_characteristics import (
    BRONZE_FILE_NAME as DFE_BRONZE_FILE_NAME,
)
from civitas.infrastructure.pipelines.dfe_characteristics import (
    DfeCharacteristicsPipeline,
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


def test_dfe_download_writes_contract_version_to_metadata(tmp_path: Path) -> None:
    fixture = FIXTURES_ROOT / "dfe_characteristics" / "school_characteristics_valid.csv"
    pipeline = DfeCharacteristicsPipeline(
        engine=None,
        source_dataset_id="dataset-1",
        source_csv=str(fixture),
    )
    context = _context(PipelineSource.DFE_CHARACTERISTICS, tmp_path / "bronze")

    pipeline.download(context)

    metadata_path = context.bronze_source_path / DFE_BRONZE_FILE_NAME
    payload = json.loads(metadata_path.with_suffix(".metadata.json").read_text(encoding="utf-8"))
    assert payload["normalization_contract_version"] == dfe_contract.CONTRACT_VERSION


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
