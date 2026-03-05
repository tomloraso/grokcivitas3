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
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import dfe_workforce as workforce_contract

RELEASE_PAGE_URL_TEMPLATE = (
    "https://explore-education-statistics.service.gov.uk/find-statistics/"
    "{publication_slug}/{release_slug}"
)
DOWNLOAD_URL_TEMPLATE = (
    "https://content.explore-education-statistics.service.gov.uk/api/releases/"
    "{release_version_id}/files/{file_id}"
)
BRONZE_MANIFEST_FILE_NAME = "dfe_workforce.manifest.json"
DEFAULT_RELEASE_SLUGS: tuple[str, ...] = ("2022", "2023", "2024")
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
    fallback_file_id: str | None = None
    fallback_file_name: str | None = None


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
    pupil_teacher_ratio: float | None
    supply_staff_pct: float | None
    teachers_3plus_years_pct: float | None
    teacher_turnover_pct: float | None
    qts_pct: float | None
    qualifications_level6_plus_pct: float | None
    headteacher_name: str | None
    headteacher_start_date: date | None
    headteacher_tenure_years: float | None
    leadership_turnover_score: float | None
    source_dataset_id: str
    source_dataset_version: str | None


class DfeWorkforcePipeline:
    source = PipelineSource.DFE_WORKFORCE

    def __init__(
        self,
        engine: Engine | None,
        *,
        publication_slug: str = "school-workforce-in-england",
        release_slugs: tuple[str, ...] = DEFAULT_RELEASE_SLUGS,
        lookback_years: int = DEFAULT_LOOKBACK_YEARS,
        strict_mode: bool = True,
        fetcher: Callable[[str], str] | None = None,
    ) -> None:
        if lookback_years <= 0:
            raise ValueError("DfE workforce lookback years must be greater than 0.")
        normalized_slugs = tuple(_normalize_release_slug(item) for item in release_slugs)
        if not normalized_slugs:
            raise ValueError("At least one release slug is required.")
        self._engine = engine
        self._publication_slug = publication_slug.strip()
        self._release_slugs = normalized_slugs
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
        assets: list[_ManifestAsset] = []
        downloaded_rows = 0
        for descriptor in descriptors:
            selected_file_id = descriptor.file_id
            selected_file_name = descriptor.file_name
            csv_payload = self._fetch_text(
                DOWNLOAD_URL_TEMPLATE.format(
                    release_version_id=descriptor.release_version_id,
                    file_id=selected_file_id,
                )
            )
            if (
                descriptor.fallback_file_id is not None
                and _count_csv_rows_from_text(csv_payload) == 0
            ):
                fallback_payload = self._fetch_text(
                    DOWNLOAD_URL_TEMPLATE.format(
                        release_version_id=descriptor.release_version_id,
                        file_id=descriptor.fallback_file_id,
                    )
                )
                if _count_csv_rows_from_text(fallback_payload) > 0:
                    selected_file_id = descriptor.fallback_file_id
                    if descriptor.fallback_file_name is not None:
                        selected_file_name = descriptor.fallback_file_name
                    csv_payload = fallback_payload

            bronze_file_name = _build_bronze_file_name(
                release_slug=descriptor.release_slug,
                file_id=selected_file_id,
            )
            bronze_file_path = context.bronze_source_path / bronze_file_name
            bronze_file_path.write_text(csv_payload, encoding="utf-8")
            row_count = _count_csv_rows(bronze_file_path)
            downloaded_rows += row_count
            assets.append(
                _ManifestAsset(
                    publication_slug=descriptor.publication_slug,
                    release_slug=descriptor.release_slug,
                    release_version_id=descriptor.release_version_id,
                    file_id=selected_file_id,
                    file_name=selected_file_name,
                    bronze_file_name=bronze_file_name,
                    downloaded_at=datetime.now(timezone.utc).isoformat(),
                    sha256=_sha256_file(bronze_file_path),
                    row_count=row_count,
                )
            )

        manifest_path.write_text(
            json.dumps(
                {
                    "downloaded_at": datetime.now(timezone.utc).isoformat(),
                    "normalization_contract_version": workforce_contract.CONTRACT_VERSION,
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
                        for asset in assets
                    ],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return downloaded_rows

    def stage(self, context: PipelineRunContext) -> StageResult:
        if self._engine is None:
            raise ValueError("Pipeline engine is required for stage.")

        manifest_assets = _load_manifest_assets(
            context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
        )
        if len(manifest_assets) == 0:
            raise FileNotFoundError("DfE workforce manifest is missing; run download first.")

        rows_by_key: dict[tuple[str, str], _StagedRow] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        for asset in manifest_assets:
            csv_path = context.bronze_source_path / asset.bronze_file_name
            with csv_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
                reader = csv.DictReader(file_handle)
                for raw_row in reader:
                    if not _is_school_level_row(raw_row):
                        continue
                    normalized_row, rejection = workforce_contract.normalize_row(
                        raw_row,
                        release_slug=asset.release_slug,
                        release_version_id=asset.release_version_id,
                        file_id=asset.file_id,
                    )
                    if normalized_row is None:
                        if rejection is not None:
                            rejected_rows.append((rejection, dict(raw_row)))
                        continue
                    staged = _StagedRow(
                        urn=normalized_row["urn"],
                        academic_year=normalized_row["academic_year"],
                        pupil_teacher_ratio=normalized_row["pupil_teacher_ratio"],
                        supply_staff_pct=normalized_row["supply_staff_pct"],
                        teachers_3plus_years_pct=normalized_row["teachers_3plus_years_pct"],
                        teacher_turnover_pct=normalized_row["teacher_turnover_pct"],
                        qts_pct=normalized_row["qts_pct"],
                        qualifications_level6_plus_pct=normalized_row[
                            "qualifications_level6_plus_pct"
                        ],
                        headteacher_name=normalized_row["headteacher_name"],
                        headteacher_start_date=normalized_row["headteacher_start_date"],
                        headteacher_tenure_years=normalized_row["headteacher_tenure_years"],
                        leadership_turnover_score=normalized_row["leadership_turnover_score"],
                        source_dataset_id=normalized_row["source_dataset_id"],
                        source_dataset_version=normalized_row["source_dataset_version"],
                    )
                    key = (staged.urn, staged.academic_year)
                    existing = rows_by_key.get(key)
                    rows_by_key[key] = (
                        _merge_staged_rows(existing=existing, incoming=staged)
                        if existing is not None
                        else staged
                    )

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
                        pupil_teacher_ratio double precision NULL,
                        supply_staff_pct double precision NULL,
                        teachers_3plus_years_pct double precision NULL,
                        teacher_turnover_pct double precision NULL,
                        qts_pct double precision NULL,
                        qualifications_level6_plus_pct double precision NULL,
                        headteacher_name text NULL,
                        headteacher_start_date date NULL,
                        headteacher_tenure_years double precision NULL,
                        leadership_turnover_score double precision NULL,
                        source_dataset_id text NOT NULL,
                        source_dataset_version text NULL,
                        PRIMARY KEY (urn, academic_year)
                    )
                    """
                )
            )
            if staged_rows:
                insert = text(
                    f"""
                    INSERT INTO staging.{staging_table_name} (
                        urn, academic_year, pupil_teacher_ratio, supply_staff_pct,
                        teachers_3plus_years_pct, teacher_turnover_pct, qts_pct,
                        qualifications_level6_plus_pct, headteacher_name, headteacher_start_date,
                        headteacher_tenure_years, leadership_turnover_score,
                        source_dataset_id, source_dataset_version
                    ) VALUES (
                        :urn, :academic_year, :pupil_teacher_ratio, :supply_staff_pct,
                        :teachers_3plus_years_pct, :teacher_turnover_pct, :qts_pct,
                        :qualifications_level6_plus_pct, :headteacher_name, :headteacher_start_date,
                        :headteacher_tenure_years, :leadership_turnover_score,
                        :source_dataset_id, :source_dataset_version
                    )
                    ON CONFLICT (urn, academic_year) DO UPDATE SET
                        pupil_teacher_ratio = EXCLUDED.pupil_teacher_ratio,
                        supply_staff_pct = EXCLUDED.supply_staff_pct,
                        teachers_3plus_years_pct = EXCLUDED.teachers_3plus_years_pct,
                        teacher_turnover_pct = EXCLUDED.teacher_turnover_pct,
                        qts_pct = EXCLUDED.qts_pct,
                        qualifications_level6_plus_pct = EXCLUDED.qualifications_level6_plus_pct,
                        headteacher_name = EXCLUDED.headteacher_name,
                        headteacher_start_date = EXCLUDED.headteacher_start_date,
                        headteacher_tenure_years = EXCLUDED.headteacher_tenure_years,
                        leadership_turnover_score = EXCLUDED.leadership_turnover_score,
                        source_dataset_id = EXCLUDED.source_dataset_id,
                        source_dataset_version = EXCLUDED.source_dataset_version
                    """
                )
                for row_chunk in chunked(staged_rows, context.stage_chunk_size):
                    connection.execute(insert, [row.__dict__ for row in row_chunk])

            if rejected_rows:
                rejection_insert = text(
                    """
                    INSERT INTO pipeline_rejections (
                        run_id, source, stage, reason_code, raw_record
                    ) VALUES (
                        :run_id, :source, 'stage', :reason_code, CAST(:raw_record AS jsonb)
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
            contract_version=workforce_contract.CONTRACT_VERSION,
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
                        WITH workforce_upserted AS (
                            INSERT INTO school_workforce_yearly (
                                urn, academic_year, pupil_teacher_ratio, supply_staff_pct,
                                teachers_3plus_years_pct, teacher_turnover_pct, qts_pct,
                                qualifications_level6_plus_pct, source_dataset_id,
                                source_dataset_version, updated_at
                            )
                            SELECT
                                staged.urn, staged.academic_year, staged.pupil_teacher_ratio,
                                staged.supply_staff_pct, staged.teachers_3plus_years_pct,
                                staged.teacher_turnover_pct, staged.qts_pct,
                                staged.qualifications_level6_plus_pct,
                                staged.source_dataset_id, staged.source_dataset_version,
                                timezone('utc', now())
                            FROM staging.{staging_table_name} AS staged
                            INNER JOIN schools ON schools.urn = staged.urn
                            ON CONFLICT (urn, academic_year) DO UPDATE SET
                                pupil_teacher_ratio = EXCLUDED.pupil_teacher_ratio,
                                supply_staff_pct = EXCLUDED.supply_staff_pct,
                                teachers_3plus_years_pct = EXCLUDED.teachers_3plus_years_pct,
                                teacher_turnover_pct = EXCLUDED.teacher_turnover_pct,
                                qts_pct = EXCLUDED.qts_pct,
                                qualifications_level6_plus_pct =
                                    EXCLUDED.qualifications_level6_plus_pct,
                                source_dataset_id = EXCLUDED.source_dataset_id,
                                source_dataset_version = EXCLUDED.source_dataset_version,
                                updated_at = timezone('utc', now())
                            RETURNING 1
                        ),
                        leadership_latest AS (
                            SELECT DISTINCT ON (staged.urn)
                                staged.urn,
                                staged.headteacher_name,
                                staged.headteacher_start_date,
                                staged.headteacher_tenure_years,
                                staged.leadership_turnover_score,
                                staged.source_dataset_id,
                                staged.source_dataset_version
                            FROM staging.{staging_table_name} AS staged
                            INNER JOIN schools ON schools.urn = staged.urn
                            ORDER BY
                                staged.urn,
                                substring(staged.academic_year from 1 for 4)::integer DESC,
                                staged.academic_year DESC
                        ),
                        leadership_upserted AS (
                            INSERT INTO school_leadership_snapshot (
                                urn, headteacher_name, headteacher_start_date,
                                headteacher_tenure_years, leadership_turnover_score,
                                source_dataset_id, source_dataset_version, updated_at
                            )
                            SELECT
                                urn, headteacher_name, headteacher_start_date,
                                headteacher_tenure_years, leadership_turnover_score,
                                source_dataset_id, source_dataset_version,
                                timezone('utc', now())
                            FROM leadership_latest
                            ON CONFLICT (urn) DO UPDATE SET
                                headteacher_name = EXCLUDED.headteacher_name,
                                headteacher_start_date = EXCLUDED.headteacher_start_date,
                                headteacher_tenure_years = EXCLUDED.headteacher_tenure_years,
                                leadership_turnover_score = EXCLUDED.leadership_turnover_score,
                                source_dataset_id = EXCLUDED.source_dataset_id,
                                source_dataset_version = EXCLUDED.source_dataset_version,
                                updated_at = timezone('utc', now())
                            RETURNING 1
                        )
                        SELECT
                            (SELECT COUNT(*) FROM workforce_upserted)
                            + (SELECT COUNT(*) FROM leadership_upserted)
                        """
                    )
                ).scalar_one()
            )
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
        return promoted_rows

    def _discover_release_files(self) -> tuple[_ReleaseFileDescriptor, ...]:
        descriptors: list[_ReleaseFileDescriptor] = []
        for release_slug in tuple(dict.fromkeys(self._release_slugs))[-self._lookback_years :]:
            try:
                descriptors.append(self._discover_release_file(release_slug=release_slug))
            except ValueError:
                if self._strict_mode:
                    raise
        return tuple(sorted(descriptors, key=lambda item: (item.release_slug, item.file_id)))

    def _discover_release_file(self, *, release_slug: str) -> _ReleaseFileDescriptor:
        page_url = RELEASE_PAGE_URL_TEMPLATE.format(
            publication_slug=self._publication_slug,
            release_slug=release_slug,
        )
        try:
            release_page = self._fetch_text(page_url)
        except Exception as exc:
            raise ValueError(
                "Unable to resolve workforce release page for "
                f"{self._publication_slug}/{release_slug}."
            ) from exc
        release_version = _parse_release_version_from_page(release_page)
        release_version_id = _required_str(release_version.get("id"), "Missing release version id.")
        download_files = release_version.get("downloadFiles")
        if not isinstance(download_files, list):
            raise ValueError("Release page is missing downloadFiles.")
        size_school_level = _select_file_by_name(
            download_files,
            name_fragments=("size of the school workforce", "school level"),
        )
        pupil_teacher_ratios = _select_file_by_name(
            download_files,
            name_fragments=("pupil to teacher ratios", "school level"),
        )
        selected = (
            size_school_level
            or pupil_teacher_ratios
            or _select_workforce_school_level_file(download_files)
        )
        if selected is None:
            raise ValueError("No school-level workforce file found.")
        selected_file_id = _required_str(selected.get("id"), "Selected workforce file has no id.")
        selected_file_name = _required_str(
            selected.get("name"), "Selected workforce file has no name."
        )
        fallback_file_id: str | None = None
        fallback_file_name: str | None = None
        if (
            size_school_level is not None
            and pupil_teacher_ratios is not None
            and selected_file_id
            == _required_str(size_school_level.get("id"), "Selected workforce file has no id.")
        ):
            fallback_file_id = _required_str(
                pupil_teacher_ratios.get("id"),
                "Fallback workforce file has no id.",
            )
            fallback_file_name = _required_str(
                pupil_teacher_ratios.get("name"),
                "Fallback workforce file has no name.",
            )
        return _ReleaseFileDescriptor(
            publication_slug=self._publication_slug,
            release_slug=release_slug,
            release_version_id=release_version_id,
            file_id=selected_file_id,
            file_name=selected_file_name,
            fallback_file_id=fallback_file_id,
            fallback_file_name=fallback_file_name,
        )

    @staticmethod
    def _staging_table_name(context: PipelineRunContext) -> str:
        return f"dfe_workforce__{context.run_id.hex}"


def _is_school_level_row(raw_row: dict[str, str]) -> bool:
    level = (raw_row.get("geographic_level") or "").strip().casefold()
    if level and level != "school":
        return False
    time_identifier = (raw_row.get("time_identifier") or "").strip().casefold()
    return not (time_identifier and time_identifier != "academic year")


def _merge_staged_rows(*, existing: _StagedRow, incoming: _StagedRow) -> _StagedRow:
    return _StagedRow(
        urn=existing.urn,
        academic_year=existing.academic_year,
        pupil_teacher_ratio=(
            incoming.pupil_teacher_ratio
            if incoming.pupil_teacher_ratio is not None
            else existing.pupil_teacher_ratio
        ),
        supply_staff_pct=(
            incoming.supply_staff_pct
            if incoming.supply_staff_pct is not None
            else existing.supply_staff_pct
        ),
        teachers_3plus_years_pct=(
            incoming.teachers_3plus_years_pct
            if incoming.teachers_3plus_years_pct is not None
            else existing.teachers_3plus_years_pct
        ),
        teacher_turnover_pct=(
            incoming.teacher_turnover_pct
            if incoming.teacher_turnover_pct is not None
            else existing.teacher_turnover_pct
        ),
        qts_pct=incoming.qts_pct if incoming.qts_pct is not None else existing.qts_pct,
        qualifications_level6_plus_pct=(
            incoming.qualifications_level6_plus_pct
            if incoming.qualifications_level6_plus_pct is not None
            else existing.qualifications_level6_plus_pct
        ),
        headteacher_name=(
            incoming.headteacher_name
            if incoming.headteacher_name is not None
            else existing.headteacher_name
        ),
        headteacher_start_date=(
            incoming.headteacher_start_date
            if incoming.headteacher_start_date is not None
            else existing.headteacher_start_date
        ),
        headteacher_tenure_years=(
            incoming.headteacher_tenure_years
            if incoming.headteacher_tenure_years is not None
            else existing.headteacher_tenure_years
        ),
        leadership_turnover_score=(
            incoming.leadership_turnover_score
            if incoming.leadership_turnover_score is not None
            else existing.leadership_turnover_score
        ),
        source_dataset_id=incoming.source_dataset_id,
        source_dataset_version=incoming.source_dataset_version,
    )


def _parse_release_version_from_page(html: str) -> dict[str, object]:
    match = _NEXT_DATA_PATTERN.search(html)
    if match is None:
        raise ValueError("Release page HTML does not contain __NEXT_DATA__ payload.")
    payload = json.loads(match.group("payload"))
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


def _select_workforce_school_level_file(
    download_files: Sequence[object],
) -> dict[str, object] | None:
    preferred: list[dict[str, object]] = []
    fallback: list[dict[str, object]] = []
    for item in download_files:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        normalized = name.casefold()
        if "school level" not in normalized:
            continue
        fallback.append(item)
        if any(token in normalized for token in ("workforce", "teacher", "staff")):
            preferred.append(item)
    selected = preferred or fallback
    if not selected:
        return None
    selected.sort(key=lambda item: str(item.get("id") or ""))
    return selected[0]


def _select_file_by_name(
    download_files: Sequence[object],
    *,
    name_fragments: tuple[str, ...],
) -> dict[str, object] | None:
    candidates: list[dict[str, object]] = []
    for item in download_files:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        normalized_name = name.casefold()
        if not all(fragment in normalized_name for fragment in name_fragments):
            continue
        extension = item.get("extension")
        if isinstance(extension, str) and extension.casefold() != "csv":
            continue
        file_type = item.get("type")
        if isinstance(file_type, str) and file_type.casefold() != "data":
            continue
        candidates.append(item)

    if not candidates:
        return None
    candidates.sort(key=lambda item: str(item.get("id") or ""))
    return candidates[0]


def _normalize_release_slug(value: str) -> str:
    normalized = value.strip().casefold()
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", normalized):
        raise ValueError(f"Invalid release slug '{value}'.")
    return normalized


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


def _build_bronze_file_name(*, release_slug: str, file_id: str) -> str:
    return f"dfe_workforce_{release_slug.replace('-', '_')}_{file_id}.csv"


def _clear_existing_bronze_files(bronze_source_path: Path) -> None:
    for path in bronze_source_path.glob("*"):
        if path.is_file():
            path.unlink()


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
        return max(0, sum(1 for _ in csv.reader(file_handle)) - 1)


def _count_csv_rows_from_text(payload: str) -> int:
    if not payload.strip():
        return 0
    return max(0, sum(1 for _ in csv.reader(payload.splitlines())) - 1)


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
    if raw_bytes.startswith(b"\x1f\x8b"):
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
    assets_payload = payload.get("assets") if isinstance(payload, dict) else None
    if not isinstance(assets_payload, list):
        return ()

    assets: list[_ManifestAsset] = []
    for item in assets_payload:
        if not isinstance(item, dict):
            continue
        try:
            assets.append(
                _ManifestAsset(
                    publication_slug=_required_str(item.get("publication_slug"), "missing"),
                    release_slug=_required_str(item.get("release_slug"), "missing"),
                    release_version_id=_required_str(item.get("release_version_id"), "missing"),
                    file_id=_required_str(item.get("file_id"), "missing"),
                    file_name=_required_str(item.get("file_name"), "missing"),
                    bronze_file_name=_required_str(item.get("bronze_file_name"), "missing"),
                    downloaded_at=_required_str(item.get("downloaded_at"), "missing"),
                    sha256=_required_str(item.get("sha256"), "missing"),
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
        path = bronze_source_path / asset.bronze_file_name
        if not path.exists() or _sha256_file(path) != asset.sha256:
            return False
    return True


def _select_lookback_years(*, years: tuple[str, ...], lookback_years: int) -> set[str]:
    sorted_years = sorted(years, key=_academic_year_sort_key)
    return set(sorted_years[-lookback_years:]) if lookback_years > 0 else set()


def _academic_year_sort_key(value: str) -> tuple[int, str]:
    try:
        start_year = int(value.split("/", maxsplit=1)[0])
    except (ValueError, IndexError):
        start_year = -1
    return start_year, value
