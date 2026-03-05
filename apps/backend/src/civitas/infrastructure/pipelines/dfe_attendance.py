from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import urllib.request
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import dfe_attendance as attendance_contract

RELEASE_PAGE_URL_TEMPLATE = (
    "https://explore-education-statistics.service.gov.uk/find-statistics/"
    "{publication_slug}/{release_slug}"
)
DOWNLOAD_URL_TEMPLATE = (
    "https://content.explore-education-statistics.service.gov.uk/api/releases/"
    "{release_version_id}/files/{file_id}"
)

BRONZE_MANIFEST_FILE_NAME = "dfe_attendance.manifest.json"
DEFAULT_RELEASE_SLUGS: tuple[str, ...] = (
    "2021-22",
    "2022-23",
    "2023-24",
)
DEFAULT_LOOKBACK_YEARS = 3
_NEXT_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(?P<payload>.*?)</script>',
    flags=re.DOTALL,
)


@dataclass(frozen=True)
class _ReleaseFileDescriptor:
    publication_slug: str
    release_slug: str
    release_version_id: str
    file_id: str
    file_name: str


@dataclass(frozen=True)
class _ManifestAsset:
    publication_slug: str
    release_slug: str
    release_version_id: str
    file_id: str
    file_name: str
    bronze_file_name: str
    downloaded_at: str
    sha256: str
    row_count: int


@dataclass(frozen=True)
class _StagedRow:
    urn: str
    academic_year: str
    overall_attendance_pct: float | None
    overall_absence_pct: float | None
    persistent_absence_pct: float | None
    source_dataset_id: str
    source_dataset_version: str | None


class DfeAttendancePipeline:
    source = PipelineSource.DFE_ATTENDANCE

    def __init__(
        self,
        engine: Engine | None,
        *,
        publication_slug: str = "pupil-absence-in-schools-in-england",
        release_slugs: tuple[str, ...] = DEFAULT_RELEASE_SLUGS,
        lookback_years: int = DEFAULT_LOOKBACK_YEARS,
        strict_mode: bool = True,
        fetcher: Callable[[str], str] | None = None,
    ) -> None:
        if lookback_years <= 0:
            raise ValueError("DfE attendance lookback years must be greater than 0.")
        normalized_release_slugs = tuple(_normalize_release_slug(item) for item in release_slugs)
        if not normalized_release_slugs:
            raise ValueError("At least one release slug is required.")
        self._engine = engine
        self._publication_slug = publication_slug.strip()
        self._release_slugs = normalized_release_slugs
        self._lookback_years = lookback_years
        self._strict_mode = strict_mode
        self._fetch_text = fetcher or _download_text

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME

        cached_assets = _load_manifest_assets(manifest_path)
        if cached_assets and _manifest_assets_exist(
            cached_assets, bronze_source_path=context.bronze_source_path
        ):
            return sum(asset.row_count for asset in cached_assets)

        _clear_existing_bronze_files(context.bronze_source_path)

        descriptors = self._discover_release_files()
        downloaded_assets: list[_ManifestAsset] = []
        total_rows = 0
        for descriptor in descriptors:
            bronze_file_name = _build_bronze_file_name(descriptor)
            bronze_file_path = context.bronze_source_path / bronze_file_name
            download_url = DOWNLOAD_URL_TEMPLATE.format(
                release_version_id=descriptor.release_version_id,
                file_id=descriptor.file_id,
            )
            csv_text = self._fetch_text(download_url)
            bronze_file_path.write_text(csv_text, encoding="utf-8")
            row_count = _count_csv_rows(bronze_file_path)
            total_rows += row_count
            downloaded_assets.append(
                _ManifestAsset(
                    publication_slug=descriptor.publication_slug,
                    release_slug=descriptor.release_slug,
                    release_version_id=descriptor.release_version_id,
                    file_id=descriptor.file_id,
                    file_name=descriptor.file_name,
                    bronze_file_name=bronze_file_name,
                    downloaded_at=datetime.now(timezone.utc).isoformat(),
                    sha256=_sha256_file(bronze_file_path),
                    row_count=row_count,
                )
            )

        manifest_payload = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "normalization_contract_version": attendance_contract.CONTRACT_VERSION,
            "lookback_years": self._lookback_years,
            "assets": [
                {
                    "publication_slug": asset.publication_slug,
                    "release_slug": asset.release_slug,
                    "release_version_id": asset.release_version_id,
                    "file_id": asset.file_id,
                    "file_name": asset.file_name,
                    "bronze_file_name": asset.bronze_file_name,
                    "downloaded_at": asset.downloaded_at,
                    "sha256": asset.sha256,
                    "row_count": asset.row_count,
                }
                for asset in downloaded_assets
            ],
        }
        manifest_path.write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return total_rows

    def stage(self, context: PipelineRunContext) -> StageResult:
        if self._engine is None:
            raise ValueError("Pipeline engine is required for stage.")

        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
        manifest_assets = _load_manifest_assets(manifest_path)
        if len(manifest_assets) == 0:
            raise FileNotFoundError(
                f"DfE attendance manifest not found at '{manifest_path}'. Run download stage first."
            )

        rows_by_key: dict[tuple[str, str], _StagedRow] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []

        for asset in manifest_assets:
            csv_path = context.bronze_source_path / asset.bronze_file_name
            with csv_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
                reader = csv.DictReader(file_handle)
                for raw_row in reader:
                    if not _is_school_level_row(raw_row):
                        continue
                    normalized_row, rejection = attendance_contract.normalize_row(
                        raw_row,
                        release_slug=asset.release_slug,
                        release_version_id=asset.release_version_id,
                        file_id=asset.file_id,
                    )
                    if normalized_row is None:
                        if rejection is not None:
                            rejected_rows.append((rejection, dict(raw_row)))
                        continue
                    staged_row = _StagedRow(
                        urn=normalized_row["urn"],
                        academic_year=normalized_row["academic_year"],
                        overall_attendance_pct=normalized_row["overall_attendance_pct"],
                        overall_absence_pct=normalized_row["overall_absence_pct"],
                        persistent_absence_pct=normalized_row["persistent_absence_pct"],
                        source_dataset_id=normalized_row["source_dataset_id"],
                        source_dataset_version=normalized_row["source_dataset_version"],
                    )
                    rows_by_key[(staged_row.urn, staged_row.academic_year)] = staged_row

        selected_years = _select_lookback_years(
            years=tuple({row.academic_year for row in rows_by_key.values()}),
            lookback_years=self._lookback_years,
        )
        staged_rows = [row for row in rows_by_key.values() if row.academic_year in selected_years]
        staged_rows.sort(key=lambda row: (row.urn, _academic_year_sort_key(row.academic_year)))

        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
            connection.execute(
                text(
                    f"""
                    CREATE TABLE staging.{staging_table_name} (
                        urn text NOT NULL,
                        academic_year text NOT NULL,
                        overall_attendance_pct double precision NULL,
                        overall_absence_pct double precision NULL,
                        persistent_absence_pct double precision NULL,
                        source_dataset_id text NOT NULL,
                        source_dataset_version text NULL,
                        PRIMARY KEY (urn, academic_year)
                    )
                    """
                )
            )
            if staged_rows:
                staged_insert = text(
                    f"""
                    INSERT INTO staging.{staging_table_name} (
                        urn,
                        academic_year,
                        overall_attendance_pct,
                        overall_absence_pct,
                        persistent_absence_pct,
                        source_dataset_id,
                        source_dataset_version
                    ) VALUES (
                        :urn,
                        :academic_year,
                        :overall_attendance_pct,
                        :overall_absence_pct,
                        :persistent_absence_pct,
                        :source_dataset_id,
                        :source_dataset_version
                    )
                    ON CONFLICT (urn, academic_year) DO UPDATE SET
                        overall_attendance_pct = EXCLUDED.overall_attendance_pct,
                        overall_absence_pct = EXCLUDED.overall_absence_pct,
                        persistent_absence_pct = EXCLUDED.persistent_absence_pct,
                        source_dataset_id = EXCLUDED.source_dataset_id,
                        source_dataset_version = EXCLUDED.source_dataset_version
                    """
                )
                for row_chunk in chunked(staged_rows, context.stage_chunk_size):
                    connection.execute(
                        staged_insert,
                        [
                            {
                                "urn": row.urn,
                                "academic_year": row.academic_year,
                                "overall_attendance_pct": row.overall_attendance_pct,
                                "overall_absence_pct": row.overall_absence_pct,
                                "persistent_absence_pct": row.persistent_absence_pct,
                                "source_dataset_id": row.source_dataset_id,
                                "source_dataset_version": row.source_dataset_version,
                            }
                            for row in row_chunk
                        ],
                    )

            if rejected_rows:
                rejection_insert = text(
                    """
                    INSERT INTO pipeline_rejections (
                        run_id,
                        source,
                        stage,
                        reason_code,
                        raw_record
                    ) VALUES (
                        :run_id,
                        :source,
                        'stage',
                        :reason_code,
                        CAST(:raw_record AS jsonb)
                    )
                    """
                )
                for rejected_chunk in chunked(rejected_rows, context.stage_chunk_size):
                    connection.execute(
                        rejection_insert,
                        [
                            {
                                "run_id": str(context.run_id),
                                "source": context.source.value,
                                "reason_code": reason_code,
                                "raw_record": json.dumps(raw_row, ensure_ascii=True),
                            }
                            for reason_code, raw_row in rejected_chunk
                        ],
                    )

        return StageResult(
            staged_rows=len(staged_rows),
            rejected_rows=len(rejected_rows),
            contract_version=attendance_contract.CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        if self._engine is None:
            raise ValueError("Pipeline engine is required for promote.")

        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            promoted_rows = int(
                connection.execute(
                    text(
                        f"""
                        WITH upserted AS (
                            INSERT INTO school_attendance_yearly (
                                urn,
                                academic_year,
                                overall_attendance_pct,
                                overall_absence_pct,
                                persistent_absence_pct,
                                source_dataset_id,
                                source_dataset_version,
                                updated_at
                            )
                            SELECT
                                staged.urn,
                                staged.academic_year,
                                staged.overall_attendance_pct,
                                staged.overall_absence_pct,
                                staged.persistent_absence_pct,
                                staged.source_dataset_id,
                                staged.source_dataset_version,
                                timezone('utc', now())
                            FROM staging.{staging_table_name} AS staged
                            INNER JOIN schools ON schools.urn = staged.urn
                            ON CONFLICT (urn, academic_year) DO UPDATE SET
                                overall_attendance_pct = EXCLUDED.overall_attendance_pct,
                                overall_absence_pct = EXCLUDED.overall_absence_pct,
                                persistent_absence_pct = EXCLUDED.persistent_absence_pct,
                                source_dataset_id = EXCLUDED.source_dataset_id,
                                source_dataset_version = EXCLUDED.source_dataset_version,
                                updated_at = timezone('utc', now())
                            RETURNING 1
                        )
                        SELECT COUNT(*) FROM upserted
                        """
                    )
                ).scalar_one()
            )
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
        return promoted_rows

    def _discover_release_files(self) -> tuple[_ReleaseFileDescriptor, ...]:
        release_slugs = self._selected_release_slugs()
        descriptors: list[_ReleaseFileDescriptor] = []
        for release_slug in release_slugs:
            try:
                descriptors.append(self._discover_release_file(release_slug=release_slug))
            except ValueError:
                if self._strict_mode:
                    raise
        return tuple(sorted(descriptors, key=lambda item: (item.release_slug, item.file_id)))

    def _selected_release_slugs(self) -> tuple[str, ...]:
        sorted_unique = tuple(dict.fromkeys(self._release_slugs))
        return sorted_unique[-self._lookback_years :]

    def _discover_release_file(self, *, release_slug: str) -> _ReleaseFileDescriptor:
        page_url = RELEASE_PAGE_URL_TEMPLATE.format(
            publication_slug=self._publication_slug,
            release_slug=release_slug,
        )
        html = self._fetch_text(page_url)
        release_version = _parse_release_version_from_page(html)

        release_version_id = _required_str(
            release_version.get("id"),
            message=f"Missing release version id for {self._publication_slug}/{release_slug}.",
        )
        download_files = release_version.get("downloadFiles")
        if not isinstance(download_files, list):
            raise ValueError(
                f"Release page is missing downloadFiles for {self._publication_slug}/{release_slug}."
            )

        selected = _select_attendance_school_level_file(download_files)
        if selected is None:
            raise ValueError(
                f"No school-level attendance file found for {self._publication_slug}/{release_slug}."
            )

        return _ReleaseFileDescriptor(
            publication_slug=self._publication_slug,
            release_slug=release_slug,
            release_version_id=release_version_id,
            file_id=_required_str(selected.get("id"), "Selected attendance file has no id."),
            file_name=_required_str(selected.get("name"), "Selected attendance file has no name."),
        )

    @staticmethod
    def _staging_table_name(context: PipelineRunContext) -> str:
        return f"dfe_attendance__{context.run_id.hex}"


def _is_school_level_row(raw_row: dict[str, str]) -> bool:
    level = (raw_row.get("geographic_level") or "").strip().casefold()
    if level and level != "school":
        return False
    time_identifier = (raw_row.get("time_identifier") or "").strip().casefold()
    return not (time_identifier and time_identifier != "academic year")


def _parse_release_version_from_page(html: str) -> dict[str, object]:
    match = _NEXT_DATA_PATTERN.search(html)
    if match is None:
        raise ValueError("Release page HTML does not contain __NEXT_DATA__ payload.")
    try:
        payload = json.loads(match.group("payload"))
    except json.JSONDecodeError as exc:
        raise ValueError("Release page __NEXT_DATA__ payload is invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Release page __NEXT_DATA__ payload was not an object.")

    props_payload = payload.get("props")
    if not isinstance(props_payload, dict):
        raise ValueError("Release page does not contain props payload.")
    page_props_payload = props_payload.get("pageProps")
    if not isinstance(page_props_payload, dict):
        raise ValueError("Release page does not contain pageProps payload.")
    release_version = page_props_payload.get("releaseVersion")
    if not isinstance(release_version, dict):
        raise ValueError("Release page does not contain releaseVersion payload.")
    return release_version


def _select_attendance_school_level_file(
    download_files: Sequence[object],
) -> dict[str, object] | None:
    candidates: list[dict[str, object]] = []
    for item in download_files:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        normalized_name = name.casefold()
        if "school level" not in normalized_name:
            continue
        if "absence" not in normalized_name:
            continue
        if "alternative provision" in normalized_name or "pru" in normalized_name:
            continue
        if "four year olds" in normalized_name:
            continue
        candidates.append(item)

    if not candidates:
        return None
    candidates.sort(key=lambda item: str(item.get("id") or ""))
    return candidates[0]


def _required_str(value: object, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(message)
    return value.strip()


def _parse_row_count(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise ValueError("row_count is missing or invalid.")


def _normalize_release_slug(value: str) -> str:
    normalized = value.strip()
    if not re.match(r"^\d{4}-\d{2}$", normalized):
        raise ValueError(f"Invalid release slug '{value}'.")
    return normalized


def _build_bronze_file_name(descriptor: _ReleaseFileDescriptor) -> str:
    release_slug_token = descriptor.release_slug.replace("-", "_")
    return f"dfe_attendance_{release_slug_token}_{descriptor.file_id}.csv"


def _clear_existing_bronze_files(bronze_source_path: Path) -> None:
    for path in bronze_source_path.glob("*"):
        if path.is_file():
            path.unlink()


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
        return max(0, sum(1 for _ in csv.reader(file_handle)) - 1)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "civitas-pipeline/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw_bytes = response.read()
        return _decode_response_bytes(raw_bytes, response.headers.get("Content-Encoding"))


def _decode_response_bytes(raw_bytes: bytes, content_encoding: str | None) -> str:
    encoding_value = (content_encoding or "").casefold()
    should_try_gzip = "gzip" in encoding_value or raw_bytes.startswith(b"\x1f\x8b")
    if should_try_gzip:
        with suppress(OSError):
            raw_bytes = gzip.decompress(raw_bytes)
    return raw_bytes.decode("utf-8-sig", errors="replace")


def _load_manifest_assets(manifest_path: Path) -> tuple[_ManifestAsset, ...]:
    if not manifest_path.exists():
        return ()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ()
    if not isinstance(payload, dict):
        return ()
    assets_payload = payload.get("assets")
    if not isinstance(assets_payload, list):
        return ()

    assets: list[_ManifestAsset] = []
    for item in assets_payload:
        if not isinstance(item, dict):
            continue
        try:
            assets.append(
                _ManifestAsset(
                    publication_slug=_required_str(
                        item.get("publication_slug"), "publication slug missing"
                    ),
                    release_slug=_required_str(item.get("release_slug"), "release slug missing"),
                    release_version_id=_required_str(
                        item.get("release_version_id"), "release id missing"
                    ),
                    file_id=_required_str(item.get("file_id"), "file id missing"),
                    file_name=_required_str(item.get("file_name"), "file name missing"),
                    bronze_file_name=_required_str(
                        item.get("bronze_file_name"), "bronze file missing"
                    ),
                    downloaded_at=_required_str(item.get("downloaded_at"), "downloaded at missing"),
                    sha256=_required_str(item.get("sha256"), "sha256 missing"),
                    row_count=_parse_row_count(item.get("row_count")),
                )
            )
        except (TypeError, ValueError):
            continue

    return tuple(sorted(assets, key=lambda item: (item.release_slug, item.file_id)))


def _manifest_assets_exist(
    assets: Sequence[_ManifestAsset],
    *,
    bronze_source_path: Path,
) -> bool:
    if len(assets) == 0:
        return False
    for asset in assets:
        file_path = bronze_source_path / asset.bronze_file_name
        if not file_path.exists() or not file_path.is_file():
            return False
        if _sha256_file(file_path) != asset.sha256:
            return False
    return True


def _select_lookback_years(*, years: tuple[str, ...], lookback_years: int) -> set[str]:
    sorted_years = sorted(years, key=_academic_year_sort_key)
    if lookback_years <= 0:
        return set()
    return set(sorted_years[-lookback_years:])


def _academic_year_sort_key(value: str) -> tuple[int, str]:
    try:
        start_year = int(value.split("/", maxsplit=1)[0])
    except (ValueError, IndexError):
        start_year = -1
    return start_year, value
