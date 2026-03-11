from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import urllib.request
from collections import defaultdict
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, cast
from zipfile import ZipFile

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.sql.elements import TextClause

from .base import PipelineRunContext, PipelineSource, StageResult
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
CURRENT_SOURCE_CATALOG_RELEASE_SLUG = "2024"
CURRENT_SOURCE_CATALOG_RELEASE_VERSION_ID = "ba5318f9-2f18-4ef5-8c71-a4db8546758c"
_NEXT_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(?P<payload>.*?)</script>',
    flags=re.DOTALL,
)
_LEGACY_WORKFORCE_ASSET_KIND = "legacy_workforce"
_TEACHER_CHARACTERISTICS_ASSET_KIND = "teacher_characteristics"
_SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND = "support_staff_characteristics"
_TEACHER_PAY_ASSET_KIND = "teacher_pay"
_TEACHER_ABSENCE_ASSET_KIND = "teacher_absence"
_TEACHER_VACANCIES_ASSET_KIND = "teacher_vacancies"
_THIRD_PARTY_SUPPORT_ASSET_KIND = "third_party_support"
_WORKFORCE_SIZE_ASSET_KIND = "workforce_size"
_TEACHER_TURNOVER_ASSET_KIND = "teacher_turnover"
_STAGEABLE_ASSET_KINDS = frozenset(
    {
        _LEGACY_WORKFORCE_ASSET_KIND,
        _TEACHER_CHARACTERISTICS_ASSET_KIND,
        _SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND,
        _TEACHER_PAY_ASSET_KIND,
        _TEACHER_ABSENCE_ASSET_KIND,
        _TEACHER_VACANCIES_ASSET_KIND,
        _THIRD_PARTY_SUPPORT_ASSET_KIND,
    }
)
_SKIPPABLE_SOURCE_STATUSES = frozenset({"empty", "unavailable"})
_CSV_TEXT_ENCODINGS: tuple[str, ...] = ("utf-8-sig", "cp1252", "latin-1")
_MAX_REJECTION_SAMPLES_PER_REASON = 10


@dataclass(frozen=True)
class _ReleaseFileDescriptor:
    asset_kind: str
    publication_slug: str
    release_slug: str
    release_version_id: str
    file_id: str
    file_name: str
    file_format: str = "csv"
    source_status: str | None = None


@dataclass(frozen=True)
class _ManifestAsset:
    asset_kind: str
    file_format: str
    publication_slug: str
    release_slug: str
    release_version_id: str
    file_id: str
    file_name: str
    bronze_file_name: str
    downloaded_at: str
    sha256: str
    row_count: int
    zip_entries: tuple[str, ...] = ()
    source_status: str | None = None


@dataclass
class _RejectedRowSummary:
    asset_kind: str
    reason_code: str
    rejected_count: int = 0
    sample_rows: list[dict[str, str]] = field(default_factory=list)

    def record(self, raw_row: Mapping[str, str], *, max_samples: int) -> None:
        self.rejected_count += 1
        if len(self.sample_rows) < max_samples:
            self.sample_rows.append(dict(raw_row))


@dataclass(frozen=True)
class _StageLoadPlan:
    target_table_name: str
    load_table_name: str | None
    columns: tuple[str, ...]
    key_columns: tuple[str, ...]
    merge_sql: TextClause | None
    fallback_insert_sql: TextClause


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
        fetcher: Callable[[str], bytes | str] | None = None,
        source_catalog_release_slug: str = CURRENT_SOURCE_CATALOG_RELEASE_SLUG,
        source_catalog_release_version_id: str = CURRENT_SOURCE_CATALOG_RELEASE_VERSION_ID,
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
        self._fetch_content = fetcher or _download_content
        self._source_catalog_release_slug = _normalize_release_slug(source_catalog_release_slug)
        self._source_catalog_release_version_id = source_catalog_release_version_id.strip()

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
            bronze_file_name = _build_bronze_file_name(
                release_slug=descriptor.release_slug,
                file_id=descriptor.file_id,
                file_format=descriptor.file_format,
            )
            bronze_file_path = context.bronze_source_path / bronze_file_name
            response_bytes = _ensure_bytes(
                self._fetch_content(
                    DOWNLOAD_URL_TEMPLATE.format(
                        release_version_id=descriptor.release_version_id,
                        file_id=descriptor.file_id,
                    )
                )
            )
            zip_entries = (
                tuple(_csv_entries_in_zip_bytes(response_bytes))
                if descriptor.file_format == "zip"
                else ()
            )
            row_count = _count_asset_rows_from_bytes(
                response_bytes,
                file_format=descriptor.file_format,
                zip_entries=zip_entries,
            )
            bronze_file_path.write_bytes(response_bytes)
            source_status = descriptor.source_status
            if source_status is None and row_count == 0:
                source_status = "empty"
            downloaded_rows += row_count
            assets.append(
                _ManifestAsset(
                    asset_kind=descriptor.asset_kind,
                    file_format=descriptor.file_format,
                    publication_slug=descriptor.publication_slug,
                    release_slug=descriptor.release_slug,
                    release_version_id=descriptor.release_version_id,
                    file_id=descriptor.file_id,
                    file_name=descriptor.file_name,
                    bronze_file_name=bronze_file_name,
                    downloaded_at=context.started_at.isoformat(),
                    sha256=_sha256_bytes(response_bytes),
                    row_count=row_count,
                    zip_entries=zip_entries,
                    source_status=source_status,
                )
            )

        manifest_path.write_text(
            json.dumps(
                {
                    "downloaded_at": context.started_at.isoformat(),
                    "normalization_contract_version": workforce_contract.CONTRACT_VERSION,
                    "lookback_years": self._lookback_years,
                    "assets": [
                        {
                            "asset_kind": asset.asset_kind,
                            "file_format": asset.file_format,
                            "publication_slug": asset.publication_slug,
                            "release_slug": asset.release_slug,
                            "release_version_id": asset.release_version_id,
                            "file_id": asset.file_id,
                            "file_name": asset.file_name,
                            "bronze_file_name": asset.bronze_file_name,
                            "downloaded_at": asset.downloaded_at,
                            "sha256": asset.sha256,
                            "row_count": asset.row_count,
                            "zip_entries": list(asset.zip_entries),
                            "source_status": asset.source_status,
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

        rejected_row_count = 0
        rejection_summaries: dict[tuple[str, str], _RejectedRowSummary] = {}
        staged_row_counts_by_year: dict[str, int] = defaultdict(int)
        stage_tables = self._stage_table_names(context)
        minimum_selected_academic_year_start = _minimum_selected_academic_year_start(
            release_slugs=self._selected_release_slugs(),
            lookback_years=self._lookback_years,
        )
        staged_buffers: dict[str, list[dict[str, object]]] = {
            asset_kind: [] for asset_kind in _STAGEABLE_ASSET_KINDS
        }

        with self._engine.begin() as connection:
            stage_load_plans = _create_stage_tables(
                connection=connection, stage_tables=stage_tables
            )

            for asset in manifest_assets:
                if asset.asset_kind not in _STAGEABLE_ASSET_KINDS:
                    if asset.source_status in _SKIPPABLE_SOURCE_STATUSES or asset.row_count == 0:
                        continue
                    if self._strict_mode:
                        raise ValueError(
                            f"Unsupported workforce asset kind '{asset.asset_kind}' "
                            f"for file '{asset.bronze_file_name}'."
                        )
                    continue
                if asset.source_status in _SKIPPABLE_SOURCE_STATUSES:
                    continue

                for raw_row in _iter_manifest_asset_rows(
                    context.bronze_source_path / asset.bronze_file_name,
                    file_format=asset.file_format,
                    zip_entries=asset.zip_entries,
                ):
                    if not _should_stage_raw_row(
                        raw_row,
                        asset_kind=asset.asset_kind,
                        release_slug=asset.release_slug,
                        minimum_academic_year_start=minimum_selected_academic_year_start,
                    ):
                        continue
                    normalized_row, rejection = _normalize_asset_row(asset=asset, raw_row=raw_row)
                    if normalized_row is None:
                        if rejection is not None:
                            rejected_row_count += 1
                            summary_key = (asset.asset_kind, rejection)
                            summary = rejection_summaries.get(summary_key)
                            if summary is None:
                                summary = _RejectedRowSummary(
                                    asset_kind=asset.asset_kind,
                                    reason_code=rejection,
                                )
                                rejection_summaries[summary_key] = summary
                            summary.record(
                                raw_row,
                                max_samples=_MAX_REJECTION_SAMPLES_PER_REASON,
                            )
                        continue

                    row_payload = dict(normalized_row)
                    academic_year = str(row_payload["academic_year"])
                    staged_row_counts_by_year[academic_year] += 1
                    staged_buffers[asset.asset_kind].append(row_payload)
                    if len(staged_buffers[asset.asset_kind]) >= context.stage_chunk_size:
                        _flush_stage_buffer(
                            connection=connection,
                            stage_plan=stage_load_plans[asset.asset_kind],
                            rows=staged_buffers[asset.asset_kind],
                        )
                        staged_buffers[asset.asset_kind].clear()

            for asset_kind, buffer in staged_buffers.items():
                if buffer:
                    _flush_stage_buffer(
                        connection=connection,
                        stage_plan=stage_load_plans[asset_kind],
                        rows=buffer,
                    )

            selected_years = _select_lookback_years(
                years=tuple(staged_row_counts_by_year.keys()),
                lookback_years=self._lookback_years,
            )
            _trim_stage_tables_to_selected_years(
                connection=connection,
                stage_tables=stage_tables,
                selected_years=selected_years,
            )

            if rejection_summaries:
                _persist_rejection_summaries(
                    connection=connection,
                    context=context,
                    rejection_summaries=rejection_summaries,
                )

        selected_stage_rows = sum(
            count for year, count in staged_row_counts_by_year.items() if year in selected_years
        )
        return StageResult(
            staged_rows=selected_stage_rows,
            rejected_rows=rejected_row_count,
            contract_version=workforce_contract.CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        if self._engine is None:
            raise ValueError("Pipeline engine is required for promote.")

        stage_tables = self._stage_table_names(context)
        with self._engine.begin() as connection:
            workforce_upserted = _upsert_workforce_base_rows(
                connection=connection,
                stage_tables=stage_tables,
            )
            teacher_upserted = _upsert_teacher_characteristics(
                connection=connection,
                stage_tables=stage_tables,
            )
            support_upserted = _upsert_support_staff_characteristics(
                connection=connection,
                stage_tables=stage_tables,
            )
            _apply_workforce_updates(connection=connection, stage_tables=stage_tables)
            leadership_upserted = _upsert_leadership_snapshot(
                connection=connection,
                stage_tables=stage_tables,
            )
            _drop_stage_tables(connection=connection, stage_tables=stage_tables)

        return workforce_upserted + teacher_upserted + support_upserted + leadership_upserted

    def _discover_release_files(self) -> tuple[_ReleaseFileDescriptor, ...]:
        descriptors: list[_ReleaseFileDescriptor] = []
        for release_slug in self._selected_release_slugs():
            try:
                descriptors.append(self._discover_legacy_workforce_file(release_slug=release_slug))
                descriptors.extend(self._approved_release_assets(release_slug=release_slug))
            except ValueError:
                if self._strict_mode:
                    raise
        return tuple(
            sorted(
                descriptors,
                key=lambda item: (item.release_slug, item.asset_kind, item.file_id),
            )
        )

    def _selected_release_slugs(self) -> tuple[str, ...]:
        sorted_unique = tuple(dict.fromkeys(self._release_slugs))
        return sorted_unique[-self._lookback_years :]

    def _discover_legacy_workforce_file(self, *, release_slug: str) -> _ReleaseFileDescriptor:
        page_url = RELEASE_PAGE_URL_TEMPLATE.format(
            publication_slug=self._publication_slug,
            release_slug=release_slug,
        )
        try:
            release_page = _ensure_text(self._fetch_content(page_url))
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
        if (
            size_school_level is not None
            and pupil_teacher_ratios is not None
            and selected_file_id
            == _required_str(size_school_level.get("id"), "Selected workforce file has no id.")
        ):
            fallback_payload = _ensure_text(
                self._fetch_content(
                    DOWNLOAD_URL_TEMPLATE.format(
                        release_version_id=release_version_id,
                        file_id=_required_str(
                            pupil_teacher_ratios.get("id"),
                            "Fallback workforce file has no id.",
                        ),
                    )
                )
            )
            if _count_csv_rows_from_text(fallback_payload) > 0:
                selected_file_id = _required_str(
                    pupil_teacher_ratios.get("id"),
                    "Fallback workforce file has no id.",
                )
                selected_file_name = _required_str(
                    pupil_teacher_ratios.get("name"),
                    "Fallback workforce file has no name.",
                )

        return _ReleaseFileDescriptor(
            asset_kind=_LEGACY_WORKFORCE_ASSET_KIND,
            publication_slug=self._publication_slug,
            release_slug=release_slug,
            release_version_id=release_version_id,
            file_id=selected_file_id,
            file_name=selected_file_name,
            file_format="csv",
        )

    def _approved_release_assets(self, *, release_slug: str) -> tuple[_ReleaseFileDescriptor, ...]:
        if release_slug != self._source_catalog_release_slug:
            return ()

        release_version_id = self._source_catalog_release_version_id
        return (
            _ReleaseFileDescriptor(
                asset_kind=_TEACHER_CHARACTERISTICS_ASSET_KIND,
                publication_slug=self._publication_slug,
                release_slug=release_slug,
                release_version_id=release_version_id,
                file_id="43ec3624-b83f-47e4-8941-2fd2fd6bfd3f",
                file_name="Teacher characteristics ZIP",
                file_format="zip",
            ),
            _ReleaseFileDescriptor(
                asset_kind=_SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND,
                publication_slug=self._publication_slug,
                release_slug=release_slug,
                release_version_id=release_version_id,
                file_id="89cc4c08-611b-4dd6-a370-184a205fe9d6",
                file_name="Support staff characteristics ZIP",
                file_format="zip",
            ),
            _ReleaseFileDescriptor(
                asset_kind=_TEACHER_PAY_ASSET_KIND,
                publication_slug=self._publication_slug,
                release_slug=release_slug,
                release_version_id=release_version_id,
                file_id="05001215-c1c7-4210-f9db-08dd8e3a5799",
                file_name="Teacher pay CSV",
            ),
            _ReleaseFileDescriptor(
                asset_kind=_TEACHER_ABSENCE_ASSET_KIND,
                publication_slug=self._publication_slug,
                release_slug=release_slug,
                release_version_id=release_version_id,
                file_id="9be449b9-57cf-4199-9410-08dd97c8935b",
                file_name="Teacher sickness absence CSV",
            ),
            _ReleaseFileDescriptor(
                asset_kind=_TEACHER_VACANCIES_ASSET_KIND,
                publication_slug=self._publication_slug,
                release_slug=release_slug,
                release_version_id=release_version_id,
                file_id="0edf6802-1d84-4a9d-f9bd-08dd8e3a5799",
                file_name="Teacher vacancies CSV",
            ),
            _ReleaseFileDescriptor(
                asset_kind=_THIRD_PARTY_SUPPORT_ASSET_KIND,
                publication_slug=self._publication_slug,
                release_slug=release_slug,
                release_version_id=release_version_id,
                file_id="d9fbbe2a-8106-452f-f9a7-08dd8e3a5799",
                file_name="Third-party support staff CSV",
            ),
            _ReleaseFileDescriptor(
                asset_kind=_WORKFORCE_SIZE_ASSET_KIND,
                publication_slug=self._publication_slug,
                release_slug=release_slug,
                release_version_id=release_version_id,
                file_id="ed1c5650-9e67-453d-0d91-08ddcde6ffdc",
                file_name="Size of the school workforce CSV",
            ),
            _ReleaseFileDescriptor(
                asset_kind=_TEACHER_TURNOVER_ASSET_KIND,
                publication_slug=self._publication_slug,
                release_slug=release_slug,
                release_version_id=release_version_id,
                file_id="8aab402f-9fc3-44bf-c16d-08ddd67d4d79",
                file_name="Teacher turnover school-level CSV",
            ),
        )

    @staticmethod
    def _stage_table_names(context: PipelineRunContext) -> dict[str, str]:
        run_id = context.run_id.hex
        return {
            _LEGACY_WORKFORCE_ASSET_KIND: f"dfe_workforce_legacy__{run_id}",
            _TEACHER_CHARACTERISTICS_ASSET_KIND: (
                f"dfe_workforce_teacher_characteristics__{run_id}"
            ),
            _SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND: (f"dfe_workforce_support_staff__{run_id}"),
            _TEACHER_PAY_ASSET_KIND: f"dfe_workforce_teacher_pay__{run_id}",
            _TEACHER_ABSENCE_ASSET_KIND: f"dfe_workforce_teacher_absence__{run_id}",
            _TEACHER_VACANCIES_ASSET_KIND: f"dfe_workforce_teacher_vacancies__{run_id}",
            _THIRD_PARTY_SUPPORT_ASSET_KIND: f"dfe_workforce_third_party_support__{run_id}",
        }


def _normalize_asset_row(
    *,
    asset: _ManifestAsset,
    raw_row: Mapping[str, str],
) -> tuple[Mapping[str, object] | None, str | None]:
    if asset.asset_kind == _LEGACY_WORKFORCE_ASSET_KIND:
        return workforce_contract.normalize_legacy_workforce_row(
            raw_row,
            release_slug=asset.release_slug,
            release_version_id=asset.release_version_id,
            file_id=asset.file_id,
        )
    if asset.asset_kind == _TEACHER_CHARACTERISTICS_ASSET_KIND:
        return workforce_contract.normalize_teacher_characteristics_row(
            raw_row,
            release_version_id=asset.release_version_id,
            file_id=asset.file_id,
        )
    if asset.asset_kind == _SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND:
        return workforce_contract.normalize_support_staff_characteristics_row(
            raw_row,
            release_version_id=asset.release_version_id,
            file_id=asset.file_id,
        )
    if asset.asset_kind == _TEACHER_PAY_ASSET_KIND:
        return workforce_contract.normalize_teacher_pay_row(
            raw_row,
            release_version_id=asset.release_version_id,
            file_id=asset.file_id,
        )
    if asset.asset_kind == _TEACHER_ABSENCE_ASSET_KIND:
        return workforce_contract.normalize_teacher_absence_row(
            raw_row,
            release_version_id=asset.release_version_id,
            file_id=asset.file_id,
        )
    if asset.asset_kind == _TEACHER_VACANCIES_ASSET_KIND:
        return workforce_contract.normalize_teacher_vacancy_row(
            raw_row,
            release_version_id=asset.release_version_id,
            file_id=asset.file_id,
        )
    if asset.asset_kind == _THIRD_PARTY_SUPPORT_ASSET_KIND:
        return workforce_contract.normalize_third_party_support_row(
            raw_row,
            release_version_id=asset.release_version_id,
            file_id=asset.file_id,
        )
    raise ValueError(f"Unsupported workforce asset kind '{asset.asset_kind}'.")


def _create_stage_tables(
    *,
    connection: Connection,
    stage_tables: Mapping[str, str],
) -> dict[str, _StageLoadPlan]:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
    stage_load_tables = _stage_load_table_names(stage_tables)
    for load_table_name in stage_load_tables.values():
        connection.execute(text(f"DROP TABLE IF EXISTS staging.{load_table_name}"))
    for table_name in stage_tables.values():
        connection.execute(text(f"DROP TABLE IF EXISTS staging.{table_name}"))

    connection.execute(
        text(
            f"""
            CREATE TABLE staging.{stage_tables[_LEGACY_WORKFORCE_ASSET_KIND]} (
                urn text NOT NULL,
                academic_year text NOT NULL,
                pupil_teacher_ratio double precision NULL,
                supply_staff_pct double precision NULL,
                teachers_3plus_years_pct double precision NULL,
                teacher_turnover_pct double precision NULL,
                qts_pct double precision NULL,
                qualifications_level6_plus_pct double precision NULL,
                source_dataset_id text NOT NULL,
                source_dataset_version text NULL,
                PRIMARY KEY (urn, academic_year)
            )
            """
        )
    )
    connection.execute(
        text(
            f"""
            CREATE TABLE staging.{stage_tables[_TEACHER_CHARACTERISTICS_ASSET_KIND]} (
                urn text NOT NULL,
                academic_year text NOT NULL,
                school_laestab text NULL,
                school_name text NOT NULL,
                school_type text NULL,
                characteristic_group text NOT NULL,
                characteristic text NOT NULL,
                grade text NULL,
                sex text NULL,
                age_group text NULL,
                working_pattern text NULL,
                qts_status text NULL,
                on_route text NULL,
                ethnicity_major text NULL,
                teacher_fte double precision NULL,
                teacher_headcount double precision NULL,
                teacher_fte_pct double precision NULL,
                teacher_headcount_pct double precision NULL,
                source_dataset_id text NOT NULL,
                source_dataset_version text NULL,
                PRIMARY KEY (urn, academic_year, characteristic_group, characteristic)
            )
            """
        )
    )
    connection.execute(
        text(
            f"""
            CREATE TABLE staging.{stage_tables[_SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND]} (
                urn text NOT NULL,
                academic_year text NOT NULL,
                school_laestab text NULL,
                school_name text NOT NULL,
                school_type text NULL,
                post text NOT NULL,
                sex text NOT NULL,
                ethnicity_major text NOT NULL,
                support_staff_fte double precision NULL,
                support_staff_headcount double precision NULL,
                source_dataset_id text NOT NULL,
                source_dataset_version text NULL,
                PRIMARY KEY (urn, academic_year, post, sex, ethnicity_major)
            )
            """
        )
    )
    connection.execute(
        text(
            f"""
            CREATE TABLE staging.{stage_tables[_TEACHER_PAY_ASSET_KIND]} (
                urn text NOT NULL,
                academic_year text NOT NULL,
                teacher_headcount_all double precision NULL,
                teacher_average_mean_salary_gbp double precision NULL,
                teacher_average_median_salary_gbp double precision NULL,
                teachers_on_leadership_pay_range_pct double precision NULL,
                source_dataset_id text NOT NULL,
                source_dataset_version text NULL,
                PRIMARY KEY (urn, academic_year)
            )
            """
        )
    )
    connection.execute(
        text(
            f"""
            CREATE TABLE staging.{stage_tables[_TEACHER_ABSENCE_ASSET_KIND]} (
                urn text NOT NULL,
                academic_year text NOT NULL,
                teachers_taking_absence_count double precision NULL,
                teacher_absence_pct double precision NULL,
                teacher_absence_days_total double precision NULL,
                teacher_absence_days_average double precision NULL,
                teacher_absence_days_average_all_teachers double precision NULL,
                source_dataset_id text NOT NULL,
                source_dataset_version text NULL,
                PRIMARY KEY (urn, academic_year)
            )
            """
        )
    )
    connection.execute(
        text(
            f"""
            CREATE TABLE staging.{stage_tables[_TEACHER_VACANCIES_ASSET_KIND]} (
                urn text NOT NULL,
                academic_year text NOT NULL,
                teacher_vacancy_count double precision NULL,
                teacher_vacancy_rate double precision NULL,
                teacher_tempfilled_vacancy_count double precision NULL,
                teacher_tempfilled_vacancy_rate double precision NULL,
                source_dataset_id text NOT NULL,
                source_dataset_version text NULL,
                PRIMARY KEY (urn, academic_year)
            )
            """
        )
    )
    connection.execute(
        text(
            f"""
            CREATE TABLE staging.{stage_tables[_THIRD_PARTY_SUPPORT_ASSET_KIND]} (
                urn text NOT NULL,
                academic_year text NOT NULL,
                school_name text NULL,
                post text NOT NULL,
                headcount double precision NULL,
                source_dataset_id text NOT NULL,
                source_dataset_version text NULL,
                PRIMARY KEY (urn, academic_year, post)
            )
            """
        )
    )

    load_table_names: dict[str, str | None] = {
        asset_kind: None for asset_kind in _STAGEABLE_ASSET_KINDS
    }
    if _supports_postgres_copy(connection=connection):
        for asset_kind, table_name in stage_tables.items():
            load_table_name = stage_load_tables[asset_kind]
            connection.execute(
                text(f"CREATE TABLE staging.{load_table_name} (LIKE staging.{table_name})")
            )
            connection.execute(
                text(
                    f"""
                    ALTER TABLE staging.{load_table_name}
                    ADD COLUMN load_ordinal bigserial NOT NULL
                    """
                )
            )
            load_table_names[asset_kind] = load_table_name

    return {
        _LEGACY_WORKFORCE_ASSET_KIND: _build_stage_load_plan(
            target_table_name=stage_tables[_LEGACY_WORKFORCE_ASSET_KIND],
            load_table_name=load_table_names[_LEGACY_WORKFORCE_ASSET_KIND],
            columns=(
                "urn",
                "academic_year",
                "pupil_teacher_ratio",
                "supply_staff_pct",
                "teachers_3plus_years_pct",
                "teacher_turnover_pct",
                "qts_pct",
                "qualifications_level6_plus_pct",
                "source_dataset_id",
                "source_dataset_version",
            ),
            key_columns=("urn", "academic_year"),
        ),
        _TEACHER_CHARACTERISTICS_ASSET_KIND: _build_stage_load_plan(
            target_table_name=stage_tables[_TEACHER_CHARACTERISTICS_ASSET_KIND],
            load_table_name=load_table_names[_TEACHER_CHARACTERISTICS_ASSET_KIND],
            columns=(
                "urn",
                "academic_year",
                "school_laestab",
                "school_name",
                "school_type",
                "characteristic_group",
                "characteristic",
                "grade",
                "sex",
                "age_group",
                "working_pattern",
                "qts_status",
                "on_route",
                "ethnicity_major",
                "teacher_fte",
                "teacher_headcount",
                "teacher_fte_pct",
                "teacher_headcount_pct",
                "source_dataset_id",
                "source_dataset_version",
            ),
            key_columns=("urn", "academic_year", "characteristic_group", "characteristic"),
        ),
        _SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND: _build_stage_load_plan(
            target_table_name=stage_tables[_SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND],
            load_table_name=load_table_names[_SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND],
            columns=(
                "urn",
                "academic_year",
                "school_laestab",
                "school_name",
                "school_type",
                "post",
                "sex",
                "ethnicity_major",
                "support_staff_fte",
                "support_staff_headcount",
                "source_dataset_id",
                "source_dataset_version",
            ),
            key_columns=("urn", "academic_year", "post", "sex", "ethnicity_major"),
        ),
        _TEACHER_PAY_ASSET_KIND: _build_stage_load_plan(
            target_table_name=stage_tables[_TEACHER_PAY_ASSET_KIND],
            load_table_name=load_table_names[_TEACHER_PAY_ASSET_KIND],
            columns=(
                "urn",
                "academic_year",
                "teacher_headcount_all",
                "teacher_average_mean_salary_gbp",
                "teacher_average_median_salary_gbp",
                "teachers_on_leadership_pay_range_pct",
                "source_dataset_id",
                "source_dataset_version",
            ),
            key_columns=("urn", "academic_year"),
        ),
        _TEACHER_ABSENCE_ASSET_KIND: _build_stage_load_plan(
            target_table_name=stage_tables[_TEACHER_ABSENCE_ASSET_KIND],
            load_table_name=load_table_names[_TEACHER_ABSENCE_ASSET_KIND],
            columns=(
                "urn",
                "academic_year",
                "teachers_taking_absence_count",
                "teacher_absence_pct",
                "teacher_absence_days_total",
                "teacher_absence_days_average",
                "teacher_absence_days_average_all_teachers",
                "source_dataset_id",
                "source_dataset_version",
            ),
            key_columns=("urn", "academic_year"),
        ),
        _TEACHER_VACANCIES_ASSET_KIND: _build_stage_load_plan(
            target_table_name=stage_tables[_TEACHER_VACANCIES_ASSET_KIND],
            load_table_name=load_table_names[_TEACHER_VACANCIES_ASSET_KIND],
            columns=(
                "urn",
                "academic_year",
                "teacher_vacancy_count",
                "teacher_vacancy_rate",
                "teacher_tempfilled_vacancy_count",
                "teacher_tempfilled_vacancy_rate",
                "source_dataset_id",
                "source_dataset_version",
            ),
            key_columns=("urn", "academic_year"),
        ),
        _THIRD_PARTY_SUPPORT_ASSET_KIND: _build_stage_load_plan(
            target_table_name=stage_tables[_THIRD_PARTY_SUPPORT_ASSET_KIND],
            load_table_name=load_table_names[_THIRD_PARTY_SUPPORT_ASSET_KIND],
            columns=(
                "urn",
                "academic_year",
                "school_name",
                "post",
                "headcount",
                "source_dataset_id",
                "source_dataset_version",
            ),
            key_columns=("urn", "academic_year", "post"),
        ),
    }


def _stage_load_table_names(stage_tables: Mapping[str, str]) -> dict[str, str]:
    return {
        asset_kind: f"{prefix}__{table_name.rsplit('__', maxsplit=1)[-1]}"
        for asset_kind, prefix, table_name in (
            (
                _LEGACY_WORKFORCE_ASSET_KIND,
                "dfe_wf_legacy_load",
                stage_tables[_LEGACY_WORKFORCE_ASSET_KIND],
            ),
            (
                _TEACHER_CHARACTERISTICS_ASSET_KIND,
                "dfe_wf_teacher_load",
                stage_tables[_TEACHER_CHARACTERISTICS_ASSET_KIND],
            ),
            (
                _SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND,
                "dfe_wf_support_load",
                stage_tables[_SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND],
            ),
            (
                _TEACHER_PAY_ASSET_KIND,
                "dfe_wf_pay_load",
                stage_tables[_TEACHER_PAY_ASSET_KIND],
            ),
            (
                _TEACHER_ABSENCE_ASSET_KIND,
                "dfe_wf_absence_load",
                stage_tables[_TEACHER_ABSENCE_ASSET_KIND],
            ),
            (
                _TEACHER_VACANCIES_ASSET_KIND,
                "dfe_wf_vacancy_load",
                stage_tables[_TEACHER_VACANCIES_ASSET_KIND],
            ),
            (
                _THIRD_PARTY_SUPPORT_ASSET_KIND,
                "dfe_wf_third_party_load",
                stage_tables[_THIRD_PARTY_SUPPORT_ASSET_KIND],
            ),
        )
    }


def _build_stage_load_plan(
    *,
    target_table_name: str,
    load_table_name: str | None,
    columns: tuple[str, ...],
    key_columns: tuple[str, ...],
) -> _StageLoadPlan:
    column_sql = ",\n                ".join(columns)
    values_sql = ",\n                ".join(f":{column}" for column in columns)
    key_sql = ", ".join(key_columns)
    key_order_sql = ", ".join(key_columns)
    update_assignments = ",\n                ".join(
        f"{column} = EXCLUDED.{column}" for column in columns if column not in key_columns
    )
    fallback_insert_sql = text(
        f"""
        INSERT INTO staging.{target_table_name} (
            {column_sql}
        ) VALUES (
            {values_sql}
        )
        ON CONFLICT ({key_sql}) DO UPDATE SET
            {update_assignments}
        """
    )
    merge_sql = None
    if load_table_name is not None:
        merge_sql = text(
            f"""
            INSERT INTO staging.{target_table_name} (
                {column_sql}
            )
            SELECT
                {column_sql}
            FROM (
                SELECT DISTINCT ON ({key_sql})
                    {column_sql}
                FROM staging.{load_table_name}
                ORDER BY {key_order_sql}, load_ordinal DESC
            ) AS deduped
            ON CONFLICT ({key_sql}) DO UPDATE SET
                {update_assignments}
            """
        )
    return _StageLoadPlan(
        target_table_name=target_table_name,
        load_table_name=load_table_name,
        columns=columns,
        key_columns=key_columns,
        merge_sql=merge_sql,
        fallback_insert_sql=fallback_insert_sql,
    )


def _supports_postgres_copy(*, connection: Connection) -> bool:
    if connection.dialect.name != "postgresql":
        return False
    try:
        driver_connection = connection.connection.driver_connection
    except AttributeError:
        return False
    return hasattr(driver_connection, "cursor")


def _flush_stage_buffer(
    *,
    connection: Connection,
    stage_plan: _StageLoadPlan,
    rows: Sequence[Mapping[str, object]],
) -> None:
    if len(rows) == 0:
        return
    if stage_plan.load_table_name is not None and stage_plan.merge_sql is not None:
        connection.execute(text(f"TRUNCATE TABLE staging.{stage_plan.load_table_name}"))
        _copy_rows_to_stage_load_table(connection=connection, stage_plan=stage_plan, rows=rows)
        connection.execute(stage_plan.merge_sql)
        connection.execute(text(f"TRUNCATE TABLE staging.{stage_plan.load_table_name}"))
        return
    connection.execute(stage_plan.fallback_insert_sql, list(rows))


def _copy_rows_to_stage_load_table(
    *,
    connection: Connection,
    stage_plan: _StageLoadPlan,
    rows: Sequence[Mapping[str, object]],
) -> None:
    if stage_plan.load_table_name is None:
        raise ValueError("Load table name is required for COPY-based stage loads.")
    driver_connection = cast(Any, connection.connection.driver_connection)
    copy_sql = (
        f"COPY staging.{stage_plan.load_table_name} ({', '.join(stage_plan.columns)}) FROM STDIN"
    )
    with driver_connection.cursor() as cursor, cursor.copy(copy_sql) as copy:
        for row in rows:
            copy.write_row(tuple(row.get(column) for column in stage_plan.columns))


def _trim_stage_tables_to_selected_years(
    *,
    connection: Connection,
    stage_tables: Mapping[str, str],
    selected_years: set[str],
) -> None:
    if selected_years:
        selected_years_sql = ", ".join(f"'{year}'" for year in sorted(selected_years))
        for table_name in stage_tables.values():
            connection.execute(
                text(
                    f"""
                    DELETE FROM staging.{table_name}
                    WHERE academic_year NOT IN ({selected_years_sql})
                    """
                )
            )
        return

    for table_name in stage_tables.values():
        connection.execute(text(f"DELETE FROM staging.{table_name}"))


def _upsert_workforce_base_rows(
    *,
    connection: Connection,
    stage_tables: Mapping[str, str],
) -> int:
    return int(
        connection.execute(
            text(
                f"""
                WITH legacy_rows AS (
                    SELECT urn, academic_year, max(source_dataset_id) AS source_dataset_id,
                           max(source_dataset_version) AS source_dataset_version
                    FROM staging.{stage_tables[_LEGACY_WORKFORCE_ASSET_KIND]}
                    GROUP BY urn, academic_year
                ),
                teacher_rows AS (
                    SELECT urn, academic_year, max(source_dataset_id) AS source_dataset_id,
                           max(source_dataset_version) AS source_dataset_version
                    FROM staging.{stage_tables[_TEACHER_CHARACTERISTICS_ASSET_KIND]}
                    GROUP BY urn, academic_year
                ),
                support_rows AS (
                    SELECT urn, academic_year, max(source_dataset_id) AS source_dataset_id,
                           max(source_dataset_version) AS source_dataset_version
                    FROM staging.{stage_tables[_SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND]}
                    GROUP BY urn, academic_year
                ),
                pay_rows AS (
                    SELECT urn, academic_year, max(source_dataset_id) AS source_dataset_id,
                           max(source_dataset_version) AS source_dataset_version
                    FROM staging.{stage_tables[_TEACHER_PAY_ASSET_KIND]}
                    GROUP BY urn, academic_year
                ),
                absence_rows AS (
                    SELECT urn, academic_year, max(source_dataset_id) AS source_dataset_id,
                           max(source_dataset_version) AS source_dataset_version
                    FROM staging.{stage_tables[_TEACHER_ABSENCE_ASSET_KIND]}
                    GROUP BY urn, academic_year
                ),
                vacancy_rows AS (
                    SELECT urn, academic_year, max(source_dataset_id) AS source_dataset_id,
                           max(source_dataset_version) AS source_dataset_version
                    FROM staging.{stage_tables[_TEACHER_VACANCIES_ASSET_KIND]}
                    GROUP BY urn, academic_year
                ),
                third_party_rows AS (
                    SELECT urn, academic_year, max(source_dataset_id) AS source_dataset_id,
                           max(source_dataset_version) AS source_dataset_version
                    FROM staging.{stage_tables[_THIRD_PARTY_SUPPORT_ASSET_KIND]}
                    GROUP BY urn, academic_year
                ),
                key_rows AS (
                    SELECT urn, academic_year FROM legacy_rows
                    UNION
                    SELECT urn, academic_year FROM teacher_rows
                    UNION
                    SELECT urn, academic_year FROM support_rows
                    UNION
                    SELECT urn, academic_year FROM pay_rows
                    UNION
                    SELECT urn, academic_year FROM absence_rows
                    UNION
                    SELECT urn, academic_year FROM vacancy_rows
                    UNION
                    SELECT urn, academic_year FROM third_party_rows
                ),
                workforce_upserted AS (
                    INSERT INTO school_workforce_yearly (
                        urn, academic_year, source_dataset_id, source_dataset_version, updated_at
                    )
                    SELECT
                        key_rows.urn,
                        key_rows.academic_year,
                        COALESCE(
                            legacy_rows.source_dataset_id,
                            teacher_rows.source_dataset_id,
                            support_rows.source_dataset_id,
                            pay_rows.source_dataset_id,
                            absence_rows.source_dataset_id,
                            vacancy_rows.source_dataset_id,
                            third_party_rows.source_dataset_id,
                            'workforce:unknown'
                        ),
                        COALESCE(
                            legacy_rows.source_dataset_version,
                            teacher_rows.source_dataset_version,
                            support_rows.source_dataset_version,
                            pay_rows.source_dataset_version,
                            absence_rows.source_dataset_version,
                            vacancy_rows.source_dataset_version,
                            third_party_rows.source_dataset_version
                        ),
                        timezone('utc', now())
                    FROM key_rows
                    LEFT JOIN legacy_rows
                        ON legacy_rows.urn = key_rows.urn
                       AND legacy_rows.academic_year = key_rows.academic_year
                    LEFT JOIN teacher_rows
                        ON teacher_rows.urn = key_rows.urn
                       AND teacher_rows.academic_year = key_rows.academic_year
                    LEFT JOIN support_rows
                        ON support_rows.urn = key_rows.urn
                       AND support_rows.academic_year = key_rows.academic_year
                    LEFT JOIN pay_rows
                        ON pay_rows.urn = key_rows.urn
                       AND pay_rows.academic_year = key_rows.academic_year
                    LEFT JOIN absence_rows
                        ON absence_rows.urn = key_rows.urn
                       AND absence_rows.academic_year = key_rows.academic_year
                    LEFT JOIN vacancy_rows
                        ON vacancy_rows.urn = key_rows.urn
                       AND vacancy_rows.academic_year = key_rows.academic_year
                    LEFT JOIN third_party_rows
                        ON third_party_rows.urn = key_rows.urn
                       AND third_party_rows.academic_year = key_rows.academic_year
                    INNER JOIN schools ON schools.urn = key_rows.urn
                    ON CONFLICT (urn, academic_year) DO UPDATE SET
                        source_dataset_id = EXCLUDED.source_dataset_id,
                        source_dataset_version = EXCLUDED.source_dataset_version,
                        updated_at = timezone('utc', now())
                    RETURNING 1
                )
                SELECT COUNT(*) FROM workforce_upserted
                """
            )
        ).scalar_one()
    )


def _upsert_teacher_characteristics(
    *,
    connection: Connection,
    stage_tables: Mapping[str, str],
) -> int:
    return int(
        connection.execute(
            text(
                f"""
                WITH upserted AS (
                    INSERT INTO school_teacher_characteristics_yearly (
                        urn, academic_year, characteristic_group, characteristic, grade, sex,
                        age_group, working_pattern, qts_status, on_route, ethnicity_major,
                        teacher_fte, teacher_headcount, teacher_fte_pct, teacher_headcount_pct,
                        source_dataset_id, source_dataset_version, updated_at
                    )
                    SELECT
                        staged.urn, staged.academic_year, staged.characteristic_group,
                        staged.characteristic, staged.grade, staged.sex, staged.age_group,
                        staged.working_pattern, staged.qts_status, staged.on_route,
                        staged.ethnicity_major, staged.teacher_fte, staged.teacher_headcount,
                        staged.teacher_fte_pct, staged.teacher_headcount_pct,
                        staged.source_dataset_id, staged.source_dataset_version,
                        timezone('utc', now())
                    FROM staging.{stage_tables[_TEACHER_CHARACTERISTICS_ASSET_KIND]} AS staged
                    INNER JOIN schools ON schools.urn = staged.urn
                    ON CONFLICT (urn, academic_year, characteristic_group, characteristic)
                    DO UPDATE SET
                        grade = EXCLUDED.grade,
                        sex = EXCLUDED.sex,
                        age_group = EXCLUDED.age_group,
                        working_pattern = EXCLUDED.working_pattern,
                        qts_status = EXCLUDED.qts_status,
                        on_route = EXCLUDED.on_route,
                        ethnicity_major = EXCLUDED.ethnicity_major,
                        teacher_fte = EXCLUDED.teacher_fte,
                        teacher_headcount = EXCLUDED.teacher_headcount,
                        teacher_fte_pct = EXCLUDED.teacher_fte_pct,
                        teacher_headcount_pct = EXCLUDED.teacher_headcount_pct,
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


def _upsert_support_staff_characteristics(
    *,
    connection: Connection,
    stage_tables: Mapping[str, str],
) -> int:
    return int(
        connection.execute(
            text(
                f"""
                WITH upserted AS (
                    INSERT INTO school_support_staff_yearly (
                        urn, academic_year, post, sex, ethnicity_major, support_staff_fte,
                        support_staff_headcount, source_dataset_id, source_dataset_version,
                        updated_at
                    )
                    SELECT
                        staged.urn, staged.academic_year, staged.post, staged.sex,
                        staged.ethnicity_major, staged.support_staff_fte,
                        staged.support_staff_headcount, staged.source_dataset_id,
                        staged.source_dataset_version, timezone('utc', now())
                    FROM staging.{stage_tables[_SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND]} AS staged
                    INNER JOIN schools ON schools.urn = staged.urn
                    ON CONFLICT (urn, academic_year, post, sex, ethnicity_major)
                    DO UPDATE SET
                        support_staff_fte = EXCLUDED.support_staff_fte,
                        support_staff_headcount = EXCLUDED.support_staff_headcount,
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


def _apply_workforce_updates(
    *,
    connection: Connection,
    stage_tables: Mapping[str, str],
) -> None:
    connection.execute(
        text(
            f"""
            WITH teacher_summary AS (
                SELECT
                    urn,
                    academic_year,
                    max(CASE
                        WHEN lower(characteristic_group) = 'total'
                         AND lower(characteristic) IN ('teachers', 'total')
                        THEN teacher_headcount
                    END) AS teacher_headcount_total,
                    max(CASE
                        WHEN lower(characteristic_group) = 'total'
                         AND lower(characteristic) IN ('teachers', 'total')
                        THEN teacher_fte
                    END) AS teacher_fte_total,
                    max(CASE
                        WHEN lower(characteristic_group) = 'grade'
                         AND lower(characteristic) IN ('headteacher', 'head teacher')
                        THEN teacher_headcount
                    END) AS headteacher_headcount,
                    max(CASE
                        WHEN lower(characteristic_group) = 'grade'
                         AND lower(characteristic) IN (
                            'deputy headteacher',
                            'deputy head teacher'
                        )
                        THEN teacher_headcount
                    END) AS deputy_headteacher_headcount,
                    max(CASE
                        WHEN lower(characteristic_group) = 'grade'
                         AND lower(characteristic) IN (
                            'assistant headteacher',
                            'assistant head teacher'
                        )
                        THEN teacher_headcount
                    END) AS assistant_headteacher_headcount,
                    max(CASE
                        WHEN lower(characteristic_group) = 'grade'
                         AND lower(characteristic) = 'classroom teacher'
                        THEN teacher_headcount
                    END) AS classroom_teacher_headcount,
                    max(CASE
                        WHEN lower(characteristic_group) = 'sex'
                         AND lower(characteristic) = 'female'
                        THEN teacher_headcount_pct
                    END) AS teacher_female_pct,
                    max(CASE
                        WHEN lower(characteristic_group) = 'sex'
                         AND lower(characteristic) = 'male'
                        THEN teacher_headcount_pct
                    END) AS teacher_male_pct,
                    max(CASE
                        WHEN lower(characteristic_group) = 'qts status'
                         AND lower(characteristic) IN (
                            'qualified teacher status',
                            'qualified'
                        )
                        THEN teacher_headcount_pct
                    END) AS teacher_qts_pct,
                    max(CASE
                        WHEN lower(characteristic_group) = 'qts status'
                         AND lower(characteristic) IN (
                            'unqualified teacher',
                            'unqualified'
                        )
                        THEN teacher_headcount_pct
                    END) AS teacher_unqualified_pct
                FROM staging.{stage_tables[_TEACHER_CHARACTERISTICS_ASSET_KIND]}
                GROUP BY urn, academic_year
            ),
            support_summary AS (
                SELECT
                    urn,
                    academic_year,
                    sum(support_staff_headcount) AS support_staff_headcount_total,
                    sum(support_staff_fte) AS support_staff_fte_total,
                    sum(CASE WHEN lower(post) = 'teaching assistants'
                        THEN support_staff_headcount END) AS teaching_assistant_headcount,
                    sum(CASE WHEN lower(post) = 'teaching assistants'
                        THEN support_staff_fte END) AS teaching_assistant_fte,
                    sum(CASE WHEN lower(post) = 'administrative staff'
                        THEN support_staff_headcount END) AS administrative_staff_headcount,
                    sum(CASE WHEN lower(post) = 'auxiliary staff'
                        THEN support_staff_headcount END) AS auxiliary_staff_headcount,
                    sum(CASE WHEN lower(post) = 'school business professionals'
                        THEN support_staff_headcount END)
                        AS school_business_professional_headcount,
                    sum(CASE WHEN lower(post) = 'leadership - non teacher'
                        THEN support_staff_headcount END)
                        AS leadership_non_teacher_headcount
                FROM staging.{stage_tables[_SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND]}
                GROUP BY urn, academic_year
            ),
            third_party_summary AS (
                SELECT
                    urn,
                    academic_year,
                    sum(CASE WHEN lower(post) = 'total' THEN headcount END)
                        AS third_party_support_staff_headcount
                FROM staging.{stage_tables[_THIRD_PARTY_SUPPORT_ASSET_KIND]}
                GROUP BY urn, academic_year
            ),
            update_keys AS (
                SELECT urn, academic_year FROM staging.{stage_tables[_LEGACY_WORKFORCE_ASSET_KIND]}
                UNION
                SELECT urn, academic_year FROM teacher_summary
                UNION
                SELECT urn, academic_year FROM support_summary
                UNION
                SELECT urn, academic_year FROM staging.{stage_tables[_TEACHER_PAY_ASSET_KIND]}
                UNION
                SELECT urn, academic_year FROM staging.{stage_tables[_TEACHER_ABSENCE_ASSET_KIND]}
                UNION
                SELECT urn, academic_year FROM staging.{stage_tables[_TEACHER_VACANCIES_ASSET_KIND]}
                UNION
                SELECT urn, academic_year FROM third_party_summary
            ),
            combined_updates AS (
                SELECT
                    update_keys.urn,
                    update_keys.academic_year,
                    legacy.pupil_teacher_ratio,
                    legacy.supply_staff_pct,
                    legacy.teachers_3plus_years_pct,
                    legacy.teacher_turnover_pct,
                    legacy.qts_pct,
                    legacy.qualifications_level6_plus_pct,
                    legacy.source_dataset_id AS legacy_source_dataset_id,
                    legacy.source_dataset_version AS legacy_source_dataset_version,
                    teacher_summary.teacher_headcount_total,
                    teacher_summary.teacher_fte_total,
                    teacher_summary.headteacher_headcount,
                    teacher_summary.deputy_headteacher_headcount,
                    teacher_summary.assistant_headteacher_headcount,
                    teacher_summary.classroom_teacher_headcount,
                    teacher_summary.teacher_female_pct,
                    teacher_summary.teacher_male_pct,
                    teacher_summary.teacher_qts_pct,
                    teacher_summary.teacher_unqualified_pct,
                    support_summary.support_staff_headcount_total,
                    support_summary.support_staff_fte_total,
                    support_summary.teaching_assistant_headcount,
                    support_summary.teaching_assistant_fte,
                    support_summary.administrative_staff_headcount,
                    support_summary.auxiliary_staff_headcount,
                    support_summary.school_business_professional_headcount,
                    support_summary.leadership_non_teacher_headcount,
                    pay.teacher_average_mean_salary_gbp,
                    pay.teacher_average_median_salary_gbp,
                    pay.teachers_on_leadership_pay_range_pct,
                    absence.teacher_absence_pct,
                    absence.teacher_absence_days_total,
                    absence.teacher_absence_days_average,
                    absence.teacher_absence_days_average_all_teachers,
                    vacancy.teacher_vacancy_count,
                    vacancy.teacher_vacancy_rate,
                    vacancy.teacher_tempfilled_vacancy_count,
                    vacancy.teacher_tempfilled_vacancy_rate,
                    third_party_summary.third_party_support_staff_headcount
                FROM update_keys
                LEFT JOIN staging.{stage_tables[_LEGACY_WORKFORCE_ASSET_KIND]} AS legacy
                    ON legacy.urn = update_keys.urn
                   AND legacy.academic_year = update_keys.academic_year
                LEFT JOIN teacher_summary
                    ON teacher_summary.urn = update_keys.urn
                   AND teacher_summary.academic_year = update_keys.academic_year
                LEFT JOIN support_summary
                    ON support_summary.urn = update_keys.urn
                   AND support_summary.academic_year = update_keys.academic_year
                LEFT JOIN staging.{stage_tables[_TEACHER_PAY_ASSET_KIND]} AS pay
                    ON pay.urn = update_keys.urn
                   AND pay.academic_year = update_keys.academic_year
                LEFT JOIN staging.{stage_tables[_TEACHER_ABSENCE_ASSET_KIND]} AS absence
                    ON absence.urn = update_keys.urn
                   AND absence.academic_year = update_keys.academic_year
                LEFT JOIN staging.{stage_tables[_TEACHER_VACANCIES_ASSET_KIND]} AS vacancy
                    ON vacancy.urn = update_keys.urn
                   AND vacancy.academic_year = update_keys.academic_year
                LEFT JOIN third_party_summary
                    ON third_party_summary.urn = update_keys.urn
                   AND third_party_summary.academic_year = update_keys.academic_year
            )
            UPDATE school_workforce_yearly AS workforce
            SET
                pupil_teacher_ratio = combined_updates.pupil_teacher_ratio,
                supply_staff_pct = combined_updates.supply_staff_pct,
                teachers_3plus_years_pct = combined_updates.teachers_3plus_years_pct,
                teacher_turnover_pct = combined_updates.teacher_turnover_pct,
                qts_pct = combined_updates.qts_pct,
                qualifications_level6_plus_pct = combined_updates.qualifications_level6_plus_pct,
                teacher_headcount_total = combined_updates.teacher_headcount_total,
                teacher_fte_total = combined_updates.teacher_fte_total,
                headteacher_headcount = combined_updates.headteacher_headcount,
                deputy_headteacher_headcount = combined_updates.deputy_headteacher_headcount,
                assistant_headteacher_headcount = combined_updates.assistant_headteacher_headcount,
                classroom_teacher_headcount = combined_updates.classroom_teacher_headcount,
                leadership_headcount = (
                    COALESCE(combined_updates.headteacher_headcount, 0.0)
                    + COALESCE(combined_updates.deputy_headteacher_headcount, 0.0)
                    + COALESCE(combined_updates.assistant_headteacher_headcount, 0.0)
                ),
                leadership_share_of_teachers = CASE
                    WHEN combined_updates.teacher_headcount_total IS NULL
                      OR combined_updates.teacher_headcount_total <= 0.0
                    THEN NULL
                    ELSE (
                        (
                            COALESCE(combined_updates.headteacher_headcount, 0.0)
                            + COALESCE(combined_updates.deputy_headteacher_headcount, 0.0)
                            + COALESCE(combined_updates.assistant_headteacher_headcount, 0.0)
                        ) / combined_updates.teacher_headcount_total
                    ) * 100.0
                END,
                teacher_female_pct = combined_updates.teacher_female_pct,
                teacher_male_pct = combined_updates.teacher_male_pct,
                teacher_qts_pct = combined_updates.teacher_qts_pct,
                teacher_unqualified_pct = combined_updates.teacher_unqualified_pct,
                support_staff_headcount_total = combined_updates.support_staff_headcount_total,
                support_staff_fte_total = combined_updates.support_staff_fte_total,
                teaching_assistant_headcount = combined_updates.teaching_assistant_headcount,
                teaching_assistant_fte = combined_updates.teaching_assistant_fte,
                administrative_staff_headcount = combined_updates.administrative_staff_headcount,
                auxiliary_staff_headcount = combined_updates.auxiliary_staff_headcount,
                school_business_professional_headcount =
                    combined_updates.school_business_professional_headcount,
                leadership_non_teacher_headcount =
                    combined_updates.leadership_non_teacher_headcount,
                teacher_average_mean_salary_gbp =
                    combined_updates.teacher_average_mean_salary_gbp,
                teacher_average_median_salary_gbp =
                    combined_updates.teacher_average_median_salary_gbp,
                teachers_on_leadership_pay_range_pct =
                    combined_updates.teachers_on_leadership_pay_range_pct,
                teacher_absence_pct = combined_updates.teacher_absence_pct,
                teacher_absence_days_total = combined_updates.teacher_absence_days_total,
                teacher_absence_days_average = combined_updates.teacher_absence_days_average,
                teacher_absence_days_average_all_teachers =
                    combined_updates.teacher_absence_days_average_all_teachers,
                teacher_vacancy_count = combined_updates.teacher_vacancy_count,
                teacher_vacancy_rate = combined_updates.teacher_vacancy_rate,
                teacher_tempfilled_vacancy_count =
                    combined_updates.teacher_tempfilled_vacancy_count,
                teacher_tempfilled_vacancy_rate =
                    combined_updates.teacher_tempfilled_vacancy_rate,
                third_party_support_staff_headcount =
                    combined_updates.third_party_support_staff_headcount,
                source_dataset_id = COALESCE(
                    combined_updates.legacy_source_dataset_id,
                    workforce.source_dataset_id
                ),
                source_dataset_version = COALESCE(
                    combined_updates.legacy_source_dataset_version,
                    workforce.source_dataset_version
                ),
                updated_at = timezone('utc', now())
            FROM combined_updates
            WHERE workforce.urn = combined_updates.urn
              AND workforce.academic_year = combined_updates.academic_year
            """
        )
    )


def _upsert_leadership_snapshot(
    *,
    connection: Connection,
    stage_tables: Mapping[str, str],
) -> int:
    del stage_tables
    return int(
        connection.execute(
            text(
                """
                WITH leadership_latest AS (
                    SELECT
                        schools.urn,
                        NULLIF(
                            btrim(
                                concat_ws(
                                    ' ',
                                    NULLIF(schools.head_first_name, ''),
                                    NULLIF(schools.head_last_name, '')
                                )
                            ),
                            ''
                        ) AS headteacher_name,
                        CAST(NULL AS date) AS headteacher_start_date,
                        CAST(NULL AS double precision) AS headteacher_tenure_years,
                        CAST(NULL AS double precision) AS leadership_turnover_score,
                        'gias' AS source_dataset_id,
                        CAST(NULL AS text) AS source_dataset_version
                    FROM schools
                ),
                upserted AS (
                    INSERT INTO school_leadership_snapshot (
                        urn, headteacher_name, headteacher_start_date,
                        headteacher_tenure_years, leadership_turnover_score,
                        source_dataset_id, source_dataset_version, updated_at
                    )
                    SELECT
                        urn, headteacher_name, headteacher_start_date,
                        headteacher_tenure_years, leadership_turnover_score,
                        source_dataset_id, source_dataset_version, timezone('utc', now())
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
                SELECT COUNT(*) FROM upserted
                """
            )
        ).scalar_one()
    )


def _drop_stage_tables(
    *,
    connection: Connection,
    stage_tables: Mapping[str, str],
) -> None:
    for table_name in _stage_load_table_names(stage_tables).values():
        connection.execute(text(f"DROP TABLE IF EXISTS staging.{table_name}"))
    for table_name in stage_tables.values():
        connection.execute(text(f"DROP TABLE IF EXISTS staging.{table_name}"))


def _iter_manifest_asset_rows(
    asset_path: Path,
    *,
    file_format: str,
    zip_entries: Sequence[str],
) -> Iterator[dict[str, str]]:
    normalized_format = file_format.strip().casefold()
    if normalized_format == "zip":
        with ZipFile(asset_path) as archive:
            entry_names = tuple(zip_entries) or tuple(_csv_entries_in_zip(asset_path))
            for entry_name in entry_names:
                with archive.open(entry_name, "r") as entry_handle:
                    reader = csv.DictReader(
                        StringIO(_decode_csv_text(entry_handle.read()), newline="")
                    )
                    for raw_row in reader:
                        yield _normalize_raw_csv_row(raw_row)
        return

    reader = csv.DictReader(StringIO(_decode_csv_text(asset_path.read_bytes()), newline=""))
    for raw_row in reader:
        yield _normalize_raw_csv_row(raw_row)


def _normalize_raw_csv_row(raw_row: Mapping[str, str | None]) -> dict[str, str]:
    return {str(key): "" if value is None else str(value) for key, value in raw_row.items()}


def _should_stage_raw_row(
    raw_row: Mapping[str, str],
    *,
    asset_kind: str,
    release_slug: str,
    minimum_academic_year_start: int | None,
) -> bool:
    if not _is_school_level_row(raw_row, asset_kind=asset_kind):
        return False
    if minimum_academic_year_start is None:
        return True
    academic_year = _raw_row_academic_year(raw_row, release_slug=release_slug)
    if academic_year is None:
        return True
    return _academic_year_start(academic_year) >= minimum_academic_year_start


def _is_school_level_row(raw_row: Mapping[str, str], *, asset_kind: str) -> bool:
    level = (raw_row.get("geographic_level") or "").strip().casefold()
    if level and level != "school":
        return False
    time_identifier = (raw_row.get("time_identifier") or "").strip().casefold()
    if not time_identifier:
        return True

    allowed_time_identifiers = {"academic year"}
    if asset_kind == _SUPPORT_STAFF_CHARACTERISTICS_ASSET_KIND:
        allowed_time_identifiers.add("november")
    return time_identifier in allowed_time_identifiers


def _raw_row_academic_year(
    raw_row: Mapping[str, str],
    *,
    release_slug: str,
) -> str | None:
    academic_year_raw = (raw_row.get("time_period") or raw_row.get("academic_year") or "").strip()
    if not academic_year_raw:
        academic_year_raw = release_slug.replace("-", "")
    if not academic_year_raw:
        return None
    try:
        return workforce_contract.normalize_academic_year(academic_year_raw)
    except ValueError:
        return None


def _minimum_selected_academic_year_start(
    *,
    release_slugs: tuple[str, ...],
    lookback_years: int,
) -> int | None:
    release_start_years = [
        year
        for year in (_release_slug_start_year(release_slug) for release_slug in release_slugs)
        if year is not None
    ]
    if not release_start_years:
        return None
    return max(release_start_years) - lookback_years + 1


def _release_slug_start_year(release_slug: str) -> int | None:
    match = re.match(r"^(?P<year>\d{4})(?:$|[-/])", release_slug.strip())
    if match is None:
        return None
    return int(match.group("year"))


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


def _build_bronze_file_name(*, release_slug: str, file_id: str, file_format: str) -> str:
    extension = "zip" if file_format.strip().casefold() == "zip" else "csv"
    return f"dfe_workforce_{release_slug.replace('-', '_')}_{file_id}.{extension}"


def _clear_existing_bronze_files(bronze_source_path: Path) -> None:
    for path in bronze_source_path.glob("*"):
        if path.is_file():
            path.unlink()


def _count_asset_rows(
    asset_path: Path,
    *,
    file_format: str,
    zip_entries: Sequence[str],
) -> int:
    return _count_asset_rows_from_bytes(
        asset_path.read_bytes(),
        file_format=file_format,
        zip_entries=zip_entries,
    )


def _count_asset_rows_from_bytes(
    payload: bytes,
    *,
    file_format: str,
    zip_entries: Sequence[str],
) -> int:
    normalized_format = file_format.strip().casefold()
    if normalized_format == "zip":
        total_rows = 0
        with ZipFile(BytesIO(payload)) as archive:
            entry_names = tuple(zip_entries) or tuple(_csv_entries_in_zip_bytes(payload))
            for entry_name in entry_names:
                with archive.open(entry_name, "r") as entry_handle:
                    total_rows += _count_csv_rows_from_text(_decode_csv_text(entry_handle.read()))
        return total_rows
    return _count_csv_rows_from_text(_decode_csv_text(payload))


def _count_csv_rows(csv_path: Path) -> int:
    return _count_csv_rows_from_text(_decode_csv_text(csv_path.read_bytes()))


def _count_csv_rows_from_text(payload: str) -> int:
    if not payload.strip():
        return 0
    return max(0, sum(1 for _ in csv.reader(payload.splitlines())) - 1)


def _csv_entries_in_zip(zip_path: Path) -> list[str]:
    return _csv_entries_in_zip_bytes(zip_path.read_bytes())


def _csv_entries_in_zip_bytes(payload: bytes) -> list[str]:
    with ZipFile(BytesIO(payload)) as archive:
        return sorted(
            name
            for name in archive.namelist()
            if not name.endswith("/") and name.casefold().endswith(".csv")
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _download_content(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "civitas-pipeline/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw_bytes = response.read()
    if raw_bytes.startswith(b"\x1f\x8b"):
        with suppress(OSError):
            raw_bytes = gzip.decompress(raw_bytes)
    return raw_bytes


def _ensure_bytes(value: bytes | str) -> bytes:
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8")


def _ensure_text(value: bytes | str) -> str:
    if isinstance(value, str):
        return value
    return value.decode("utf-8-sig", errors="replace")


def _decode_csv_text(value: bytes) -> str:
    last_error: UnicodeDecodeError | None = None
    for encoding in _CSV_TEXT_ENCODINGS:
        try:
            return value.decode(encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return value.decode("utf-8-sig", errors="replace")


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
            zip_entries_value = item.get("zip_entries", ())
            zip_entries = (
                tuple(
                    entry.strip()
                    for entry in zip_entries_value
                    if isinstance(entry, str) and entry.strip()
                )
                if isinstance(zip_entries_value, list)
                else ()
            )
            source_status = item.get("source_status")
            assets.append(
                _ManifestAsset(
                    asset_kind=_required_str(
                        item.get("asset_kind", _LEGACY_WORKFORCE_ASSET_KIND),
                        "missing",
                    ),
                    file_format=_required_str(item.get("file_format", "csv"), "missing"),
                    publication_slug=_required_str(item.get("publication_slug"), "missing"),
                    release_slug=_required_str(item.get("release_slug"), "missing"),
                    release_version_id=_required_str(item.get("release_version_id"), "missing"),
                    file_id=_required_str(item.get("file_id"), "missing"),
                    file_name=_required_str(item.get("file_name"), "missing"),
                    bronze_file_name=_required_str(item.get("bronze_file_name"), "missing"),
                    downloaded_at=_required_str(item.get("downloaded_at"), "missing"),
                    sha256=_required_str(item.get("sha256"), "missing"),
                    row_count=_parse_row_count(item.get("row_count")),
                    zip_entries=zip_entries,
                    source_status=str(source_status).strip() if source_status is not None else None,
                )
            )
        except (TypeError, ValueError):
            continue
    return tuple(
        sorted(
            assets,
            key=lambda item: (item.release_slug, item.asset_kind, item.file_id),
        )
    )


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


def _persist_rejection_summaries(
    *,
    connection: Connection,
    context: PipelineRunContext,
    rejection_summaries: Mapping[tuple[str, str], _RejectedRowSummary],
) -> None:
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
    connection.execute(
        rejection_insert,
        [
            {
                "run_id": str(context.run_id),
                "source": context.source.value,
                "reason_code": summary.reason_code,
                "raw_record": json.dumps(
                    {
                        "asset_kind": summary.asset_kind,
                        "rejected_count": summary.rejected_count,
                        "sample_count": len(summary.sample_rows),
                        "sample_truncated": summary.rejected_count > len(summary.sample_rows),
                        "sample_rows": summary.sample_rows,
                    },
                    ensure_ascii=True,
                ),
            }
            for summary in sorted(
                rejection_summaries.values(),
                key=lambda item: (item.asset_kind, item.reason_code),
            )
        ],
    )


def _select_lookback_years(*, years: tuple[str, ...], lookback_years: int) -> set[str]:
    sorted_years = sorted(years, key=_academic_year_sort_key)
    return set(sorted_years[-lookback_years:]) if lookback_years > 0 else set()


def _academic_year_start(value: str) -> int:
    return _academic_year_sort_key(value)[0]


def _academic_year_sort_key(value: str) -> tuple[int, str]:
    try:
        start_year = int(value.split("/", maxsplit=1)[0])
    except (ValueError, IndexError):
        start_year = -1
    return start_year, value
