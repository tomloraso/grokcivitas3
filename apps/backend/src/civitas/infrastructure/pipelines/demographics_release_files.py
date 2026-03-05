from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import urllib.request
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import demographics_sen, demographics_spc

RELEASE_PAGE_URL_TEMPLATE = (
    "https://explore-education-statistics.service.gov.uk/find-statistics/"
    "{publication_slug}/{release_slug}"
)
CONTENT_FILE_URL_TEMPLATE = (
    "https://content.explore-education-statistics.service.gov.uk/api/releases/"
    "{release_version_id}/files/{file_id}"
)

BRONZE_MANIFEST_FILE_NAME = "demographics_release_files.manifest.json"
NORMALIZATION_CONTRACT_VERSION = "demographics_release_files.v1"

_SCHOOL_LEVEL_FILE_NAME_TOKEN = "school level underlying data"
_CLASS_SIZE_FILE_NAME_TOKEN = "class size"
_NEXT_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(?P<payload>.*?)</script>',
    flags=re.IGNORECASE | re.DOTALL,
)
_ETHNICITY_PERCENTAGE_COLUMNS: tuple[str, ...] = tuple(
    f"{group.key}_pct" for group in demographics_spc.ETHNICITY_GROUP_FIELDS
)
_ETHNICITY_COUNT_COLUMNS: tuple[str, ...] = tuple(
    f"{group.key}_count" for group in demographics_spc.ETHNICITY_GROUP_FIELDS
)


class DemographicsSourceFamily(str, Enum):
    SPC = "spc"
    SEN = "sen"


@dataclass(frozen=True)
class ReleaseFileDescriptor:
    family: DemographicsSourceFamily
    publication_slug: str
    release_slug: str
    release_version_id: str
    file_id: str
    file_name: str


@dataclass(frozen=True)
class BronzeManifestAsset:
    family: DemographicsSourceFamily
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
class _SpcRecord:
    urn: str
    academic_year: str
    fsm_pct: float | None
    fsm6_pct: float | None
    disadvantaged_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None
    male_pct: float | None
    female_pct: float | None
    pupil_mobility_pct: float | None
    has_fsm6_data: bool
    has_gender_data: bool
    has_mobility_data: bool
    top_home_languages: tuple[demographics_spc.NormalizedTopLanguage, ...]
    has_top_languages_data: bool
    ethnicity_percentages: dict[str, float | None]
    ethnicity_counts: dict[str, int | None]
    has_ethnicity_data: bool
    release_version_id: str
    file_id: str


@dataclass(frozen=True)
class _SenRecord:
    urn: str
    academic_year: str
    sen_support_pct: float | None
    ehcp_pct: float | None
    total_pupils: int | None
    primary_needs: tuple[demographics_sen.NormalizedPrimaryNeed, ...]
    has_primary_need_data: bool
    release_version_id: str
    file_id: str


@dataclass(frozen=True)
class _MergedRecord:
    urn: str
    academic_year: str
    fsm_pct: float | None
    fsm6_pct: float | None
    disadvantaged_pct: float | None
    sen_pct: float | None
    sen_support_pct: float | None
    ehcp_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None
    male_pct: float | None
    female_pct: float | None
    pupil_mobility_pct: float | None
    total_pupils: int | None
    has_fsm6_data: bool
    has_gender_data: bool
    has_mobility_data: bool
    has_ethnicity_data: bool
    has_top_languages_data: bool
    has_send_primary_need_data: bool
    source_dataset_id: str
    source_dataset_version: str | None


@dataclass(frozen=True)
class _EthnicityRecord:
    urn: str
    academic_year: str
    percentages: dict[str, float | None]
    counts: dict[str, int | None]
    source_dataset_id: str
    source_dataset_version: str | None


@dataclass(frozen=True)
class _SendPrimaryNeedRecord:
    urn: str
    academic_year: str
    need_key: str
    need_label: str
    pupil_count: int | None
    percentage: float | None
    source_dataset_id: str
    source_dataset_version: str | None


@dataclass(frozen=True)
class _HomeLanguageRecord:
    urn: str
    academic_year: str
    language_key: str
    language_label: str
    rank: int
    pupil_count: int | None
    percentage: float | None
    source_dataset_id: str
    source_dataset_version: str | None


class DemographicsReleaseFilesPipeline:
    source = PipelineSource.DFE_CHARACTERISTICS

    def __init__(
        self,
        *,
        engine: Engine | None,
        spc_publication_slug: str,
        sen_publication_slug: str,
        release_slugs: Sequence[str],
        lookback_years: int,
        strict_mode: bool = True,
        fetcher: Callable[[str], str] | None = None,
    ) -> None:
        if lookback_years <= 0:
            raise ValueError("Demographics lookback years must be greater than 0.")

        cleaned_release_slugs = tuple(
            _normalize_release_slug(slug) for slug in release_slugs if slug
        )
        if not cleaned_release_slugs:
            raise ValueError("At least one demographics release slug must be configured.")

        self._engine = engine
        self._spc_publication_slug = spc_publication_slug.strip()
        self._sen_publication_slug = sen_publication_slug.strip()
        self._release_slugs = cleaned_release_slugs
        self._lookback_years = lookback_years
        self._strict_mode = strict_mode
        self._fetch_text = fetcher or _download_text

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME

        existing_assets = _load_manifest_assets(manifest_path)
        if existing_assets and all(
            (context.bronze_source_path / asset.bronze_file_name).exists()
            for asset in existing_assets
        ):
            return sum(asset.row_count for asset in existing_assets)

        descriptors = self._discover_release_files()
        if not descriptors:
            return 0

        now_iso = datetime.now(timezone.utc).isoformat()
        assets: list[BronzeManifestAsset] = []
        total_rows = 0
        for descriptor in descriptors:
            bronze_file_name = _build_bronze_file_name(descriptor)
            bronze_file_path = context.bronze_source_path / bronze_file_name
            csv_text = self._fetch_text(
                CONTENT_FILE_URL_TEMPLATE.format(
                    release_version_id=descriptor.release_version_id,
                    file_id=descriptor.file_id,
                )
            )
            bronze_file_path.write_text(csv_text, encoding="utf-8")

            row_count = _count_csv_rows(bronze_file_path)
            total_rows += row_count
            assets.append(
                BronzeManifestAsset(
                    family=descriptor.family,
                    publication_slug=descriptor.publication_slug,
                    release_slug=descriptor.release_slug,
                    release_version_id=descriptor.release_version_id,
                    file_id=descriptor.file_id,
                    file_name=descriptor.file_name,
                    bronze_file_name=bronze_file_name,
                    downloaded_at=now_iso,
                    sha256=_sha256_file(bronze_file_path),
                    row_count=row_count,
                )
            )

        manifest_payload = {
            "downloaded_at": now_iso,
            "normalization_contract_version": NORMALIZATION_CONTRACT_VERSION,
            "lookback_years": self._lookback_years,
            "assets": [
                {
                    "family": asset.family.value,
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
        assets = _load_manifest_assets(manifest_path)
        if not assets:
            raise ValueError(
                "Demographics release manifest missing assets. Run download stage before stage."
            )

        spc_rows: dict[tuple[str, str], _SpcRecord] = {}
        sen_rows: dict[tuple[str, str], _SenRecord] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []

        for asset in assets:
            bronze_file_path = context.bronze_source_path / asset.bronze_file_name
            if not bronze_file_path.exists():
                raise FileNotFoundError(
                    f"Demographics bronze file not found at '{bronze_file_path}'. "
                    "Run download stage first."
                )

            with bronze_file_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
                reader = csv.DictReader(file_handle)
                if reader.fieldnames is None:
                    raise ValueError(
                        f"Demographics CSV '{asset.bronze_file_name}' has no header row."
                    )

                if asset.family == DemographicsSourceFamily.SPC:
                    column_map = demographics_spc.validate_headers(reader.fieldnames)
                    for raw_row in reader:
                        normalized_spc, rejection = demographics_spc.normalize_row(
                            raw_row,
                            column_map=column_map,
                            release_slug=asset.release_slug,
                        )
                        if normalized_spc is None:
                            if rejection is not None:
                                rejected_rows.append((rejection, dict(raw_row)))
                            continue

                        key = (normalized_spc["urn"], normalized_spc["academic_year"])
                        spc_rows[key] = _SpcRecord(
                            urn=normalized_spc["urn"],
                            academic_year=normalized_spc["academic_year"],
                            fsm_pct=normalized_spc["fsm_pct"],
                            fsm6_pct=normalized_spc["fsm6_pct"],
                            disadvantaged_pct=normalized_spc["disadvantaged_pct"],
                            eal_pct=normalized_spc["eal_pct"],
                            first_language_english_pct=normalized_spc["first_language_english_pct"],
                            first_language_unclassified_pct=normalized_spc[
                                "first_language_unclassified_pct"
                            ],
                            male_pct=normalized_spc["male_pct"],
                            female_pct=normalized_spc["female_pct"],
                            pupil_mobility_pct=normalized_spc["pupil_mobility_pct"],
                            has_fsm6_data=normalized_spc["has_fsm6_data"],
                            has_gender_data=normalized_spc["has_gender_data"],
                            has_mobility_data=normalized_spc["has_mobility_data"],
                            top_home_languages=normalized_spc["top_home_languages"],
                            has_top_languages_data=normalized_spc["has_top_languages_data"],
                            ethnicity_percentages=normalized_spc["ethnicity_percentages"],
                            ethnicity_counts=normalized_spc["ethnicity_counts"],
                            has_ethnicity_data=normalized_spc["has_ethnicity_data"],
                            release_version_id=asset.release_version_id,
                            file_id=asset.file_id,
                        )
                else:
                    column_map = demographics_sen.validate_headers(reader.fieldnames)
                    for raw_row in reader:
                        normalized_sen, rejection = demographics_sen.normalize_row(
                            raw_row,
                            column_map=column_map,
                        )
                        if normalized_sen is None:
                            if rejection is not None:
                                rejected_rows.append((rejection, dict(raw_row)))
                            continue

                        key = (normalized_sen["urn"], normalized_sen["academic_year"])
                        sen_rows[key] = _SenRecord(
                            urn=normalized_sen["urn"],
                            academic_year=normalized_sen["academic_year"],
                            sen_support_pct=normalized_sen["sen_support_pct"],
                            ehcp_pct=normalized_sen["ehcp_pct"],
                            total_pupils=normalized_sen["total_pupils"],
                            primary_needs=normalized_sen["primary_needs"],
                            has_primary_need_data=normalized_sen["has_primary_need_data"],
                            release_version_id=asset.release_version_id,
                            file_id=asset.file_id,
                        )

        (
            merged_rows,
            ethnicity_rows,
            send_primary_need_rows,
            home_language_rows,
        ) = _merge_rows(spc_rows=spc_rows, sen_rows=sen_rows)

        staging_table_name = self._staging_table_name(context)
        ethnicity_staging_table_name = self._ethnicity_staging_table_name(context)
        send_primary_need_staging_table_name = self._send_primary_need_staging_table_name(context)
        home_language_staging_table_name = self._home_language_staging_table_name(context)
        send_primary_need_staging_table_name = self._send_primary_need_staging_table_name(context)
        home_language_staging_table_name = self._home_language_staging_table_name(context)
        ethnicity_column_definitions = ",\n                        ".join(
            [f"{column} double precision NULL" for column in _ETHNICITY_PERCENTAGE_COLUMNS]
            + [f"{column} integer NULL" for column in _ETHNICITY_COUNT_COLUMNS]
        )
        ethnicity_insert_columns = ",\n                        ".join(
            [
                "urn",
                "academic_year",
                *_ETHNICITY_PERCENTAGE_COLUMNS,
                *_ETHNICITY_COUNT_COLUMNS,
                "source_dataset_id",
                "source_dataset_version",
            ]
        )
        ethnicity_insert_values = ",\n                        ".join(
            [
                ":urn",
                ":academic_year",
                *[f":{column}" for column in _ETHNICITY_PERCENTAGE_COLUMNS],
                *[f":{column}" for column in _ETHNICITY_COUNT_COLUMNS],
                ":source_dataset_id",
                ":source_dataset_version",
            ]
        )
        ethnicity_update_columns = ",\n                        ".join(
            [f"{column} = EXCLUDED.{column}" for column in _ETHNICITY_PERCENTAGE_COLUMNS]
            + [f"{column} = EXCLUDED.{column}" for column in _ETHNICITY_COUNT_COLUMNS]
            + [
                "source_dataset_id = EXCLUDED.source_dataset_id",
                "source_dataset_version = EXCLUDED.source_dataset_version",
            ]
        )
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{ethnicity_staging_table_name}"))
            connection.execute(
                text(f"DROP TABLE IF EXISTS staging.{send_primary_need_staging_table_name}")
            )
            connection.execute(
                text(f"DROP TABLE IF EXISTS staging.{home_language_staging_table_name}")
            )
            connection.execute(
                text(
                    f"""
                    CREATE TABLE staging.{staging_table_name} (
                        urn text NOT NULL,
                        academic_year text NOT NULL,
                        fsm_pct double precision NULL,
                        fsm6_pct double precision NULL,
                        disadvantaged_pct double precision NULL,
                        sen_pct double precision NULL,
                        sen_support_pct double precision NULL,
                        ehcp_pct double precision NULL,
                        eal_pct double precision NULL,
                        first_language_english_pct double precision NULL,
                        first_language_unclassified_pct double precision NULL,
                        male_pct double precision NULL,
                        female_pct double precision NULL,
                        pupil_mobility_pct double precision NULL,
                        total_pupils integer NULL,
                        has_fsm6_data boolean NOT NULL,
                        has_gender_data boolean NOT NULL,
                        has_mobility_data boolean NOT NULL,
                        has_ethnicity_data boolean NOT NULL,
                        has_top_languages_data boolean NOT NULL,
                        has_send_primary_need_data boolean NOT NULL,
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
                    CREATE TABLE staging.{ethnicity_staging_table_name} (
                        urn text NOT NULL,
                        academic_year text NOT NULL,
                        {ethnicity_column_definitions},
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
                    CREATE TABLE staging.{send_primary_need_staging_table_name} (
                        urn text NOT NULL,
                        academic_year text NOT NULL,
                        need_key text NOT NULL,
                        need_label text NOT NULL,
                        pupil_count integer NULL,
                        percentage double precision NULL,
                        source_dataset_id text NOT NULL,
                        source_dataset_version text NULL,
                        PRIMARY KEY (urn, academic_year, need_key)
                    )
                    """
                )
            )
            connection.execute(
                text(
                    f"""
                    CREATE TABLE staging.{home_language_staging_table_name} (
                        urn text NOT NULL,
                        academic_year text NOT NULL,
                        language_key text NOT NULL,
                        language_label text NOT NULL,
                        rank integer NOT NULL,
                        pupil_count integer NULL,
                        percentage double precision NULL,
                        source_dataset_id text NOT NULL,
                        source_dataset_version text NULL,
                        PRIMARY KEY (urn, academic_year, language_key)
                    )
                    """
                )
            )
            if merged_rows:
                staged_insert = text(
                    f"""
                    INSERT INTO staging.{staging_table_name} (
                        urn,
                        academic_year,
                        fsm_pct,
                        fsm6_pct,
                        disadvantaged_pct,
                        sen_pct,
                        sen_support_pct,
                        ehcp_pct,
                        eal_pct,
                        first_language_english_pct,
                        first_language_unclassified_pct,
                        male_pct,
                        female_pct,
                        pupil_mobility_pct,
                        total_pupils,
                        has_fsm6_data,
                        has_gender_data,
                        has_mobility_data,
                        has_ethnicity_data,
                        has_top_languages_data,
                        has_send_primary_need_data,
                        source_dataset_id,
                        source_dataset_version
                    ) VALUES (
                        :urn,
                        :academic_year,
                        :fsm_pct,
                        :fsm6_pct,
                        :disadvantaged_pct,
                        :sen_pct,
                        :sen_support_pct,
                        :ehcp_pct,
                        :eal_pct,
                        :first_language_english_pct,
                        :first_language_unclassified_pct,
                        :male_pct,
                        :female_pct,
                        :pupil_mobility_pct,
                        :total_pupils,
                        :has_fsm6_data,
                        :has_gender_data,
                        :has_mobility_data,
                        :has_ethnicity_data,
                        :has_top_languages_data,
                        :has_send_primary_need_data,
                        :source_dataset_id,
                        :source_dataset_version
                    )
                    ON CONFLICT (urn, academic_year) DO UPDATE SET
                        fsm_pct = EXCLUDED.fsm_pct,
                        fsm6_pct = EXCLUDED.fsm6_pct,
                        disadvantaged_pct = EXCLUDED.disadvantaged_pct,
                        sen_pct = EXCLUDED.sen_pct,
                        sen_support_pct = EXCLUDED.sen_support_pct,
                        ehcp_pct = EXCLUDED.ehcp_pct,
                        eal_pct = EXCLUDED.eal_pct,
                        first_language_english_pct = EXCLUDED.first_language_english_pct,
                        first_language_unclassified_pct = EXCLUDED.first_language_unclassified_pct,
                        male_pct = EXCLUDED.male_pct,
                        female_pct = EXCLUDED.female_pct,
                        pupil_mobility_pct = EXCLUDED.pupil_mobility_pct,
                        total_pupils = EXCLUDED.total_pupils,
                        has_fsm6_data = EXCLUDED.has_fsm6_data,
                        has_gender_data = EXCLUDED.has_gender_data,
                        has_mobility_data = EXCLUDED.has_mobility_data,
                        has_ethnicity_data = EXCLUDED.has_ethnicity_data,
                        has_top_languages_data = EXCLUDED.has_top_languages_data,
                        has_send_primary_need_data = EXCLUDED.has_send_primary_need_data,
                        source_dataset_id = EXCLUDED.source_dataset_id,
                        source_dataset_version = EXCLUDED.source_dataset_version
                    """
                )
                for row_chunk in chunked(merged_rows, context.stage_chunk_size):
                    connection.execute(
                        staged_insert,
                        [
                            {
                                "urn": row.urn,
                                "academic_year": row.academic_year,
                                "fsm_pct": row.fsm_pct,
                                "fsm6_pct": row.fsm6_pct,
                                "disadvantaged_pct": row.disadvantaged_pct,
                                "sen_pct": row.sen_pct,
                                "sen_support_pct": row.sen_support_pct,
                                "ehcp_pct": row.ehcp_pct,
                                "eal_pct": row.eal_pct,
                                "first_language_english_pct": row.first_language_english_pct,
                                "first_language_unclassified_pct": (
                                    row.first_language_unclassified_pct
                                ),
                                "male_pct": row.male_pct,
                                "female_pct": row.female_pct,
                                "pupil_mobility_pct": row.pupil_mobility_pct,
                                "total_pupils": row.total_pupils,
                                "has_fsm6_data": row.has_fsm6_data,
                                "has_gender_data": row.has_gender_data,
                                "has_mobility_data": row.has_mobility_data,
                                "has_ethnicity_data": row.has_ethnicity_data,
                                "has_top_languages_data": row.has_top_languages_data,
                                "has_send_primary_need_data": row.has_send_primary_need_data,
                                "source_dataset_id": row.source_dataset_id,
                                "source_dataset_version": row.source_dataset_version,
                            }
                            for row in row_chunk
                        ],
                    )

            if ethnicity_rows:
                ethnicity_staged_insert = text(
                    f"""
                    INSERT INTO staging.{ethnicity_staging_table_name} (
                        {ethnicity_insert_columns}
                    ) VALUES (
                        {ethnicity_insert_values}
                    )
                    ON CONFLICT (urn, academic_year) DO UPDATE SET
                        {ethnicity_update_columns}
                    """
                )
                for ethnicity_chunk in chunked(ethnicity_rows, context.stage_chunk_size):
                    parameters: list[dict[str, object]] = []
                    for row in ethnicity_chunk:
                        payload: dict[str, object] = {
                            "urn": row.urn,
                            "academic_year": row.academic_year,
                            "source_dataset_id": row.source_dataset_id,
                            "source_dataset_version": row.source_dataset_version,
                        }
                        for group in demographics_spc.ETHNICITY_GROUP_FIELDS:
                            payload[f"{group.key}_pct"] = row.percentages.get(group.key)
                            payload[f"{group.key}_count"] = row.counts.get(group.key)
                        parameters.append(payload)
                    connection.execute(ethnicity_staged_insert, parameters)

            if send_primary_need_rows:
                send_need_insert = text(
                    f"""
                    INSERT INTO staging.{send_primary_need_staging_table_name} (
                        urn,
                        academic_year,
                        need_key,
                        need_label,
                        pupil_count,
                        percentage,
                        source_dataset_id,
                        source_dataset_version
                    ) VALUES (
                        :urn,
                        :academic_year,
                        :need_key,
                        :need_label,
                        :pupil_count,
                        :percentage,
                        :source_dataset_id,
                        :source_dataset_version
                    )
                    ON CONFLICT (urn, academic_year, need_key) DO UPDATE SET
                        need_label = EXCLUDED.need_label,
                        pupil_count = EXCLUDED.pupil_count,
                        percentage = EXCLUDED.percentage,
                        source_dataset_id = EXCLUDED.source_dataset_id,
                        source_dataset_version = EXCLUDED.source_dataset_version
                    """
                )
                for send_need_chunk in chunked(send_primary_need_rows, context.stage_chunk_size):
                    connection.execute(
                        send_need_insert,
                        [
                            {
                                "urn": row.urn,
                                "academic_year": row.academic_year,
                                "need_key": row.need_key,
                                "need_label": row.need_label,
                                "pupil_count": row.pupil_count,
                                "percentage": row.percentage,
                                "source_dataset_id": row.source_dataset_id,
                                "source_dataset_version": row.source_dataset_version,
                            }
                            for row in send_need_chunk
                        ],
                    )

            if home_language_rows:
                home_language_insert = text(
                    f"""
                    INSERT INTO staging.{home_language_staging_table_name} (
                        urn,
                        academic_year,
                        language_key,
                        language_label,
                        rank,
                        pupil_count,
                        percentage,
                        source_dataset_id,
                        source_dataset_version
                    ) VALUES (
                        :urn,
                        :academic_year,
                        :language_key,
                        :language_label,
                        :rank,
                        :pupil_count,
                        :percentage,
                        :source_dataset_id,
                        :source_dataset_version
                    )
                    ON CONFLICT (urn, academic_year, language_key) DO UPDATE SET
                        language_label = EXCLUDED.language_label,
                        rank = EXCLUDED.rank,
                        pupil_count = EXCLUDED.pupil_count,
                        percentage = EXCLUDED.percentage,
                        source_dataset_id = EXCLUDED.source_dataset_id,
                        source_dataset_version = EXCLUDED.source_dataset_version
                    """
                )
                for home_language_chunk in chunked(home_language_rows, context.stage_chunk_size):
                    connection.execute(
                        home_language_insert,
                        [
                            {
                                "urn": row.urn,
                                "academic_year": row.academic_year,
                                "language_key": row.language_key,
                                "language_label": row.language_label,
                                "rank": row.rank,
                                "pupil_count": row.pupil_count,
                                "percentage": row.percentage,
                                "source_dataset_id": row.source_dataset_id,
                                "source_dataset_version": row.source_dataset_version,
                            }
                            for row in home_language_chunk
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
            staged_rows=len(merged_rows),
            rejected_rows=len(rejected_rows),
            contract_version=(
                f"{NORMALIZATION_CONTRACT_VERSION}+"
                f"{demographics_spc.CONTRACT_VERSION}+{demographics_sen.CONTRACT_VERSION}"
            ),
        )

    def promote(self, context: PipelineRunContext) -> int:
        if self._engine is None:
            raise ValueError("Pipeline engine is required for promote.")

        staging_table_name = self._staging_table_name(context)
        ethnicity_staging_table_name = self._ethnicity_staging_table_name(context)
        send_primary_need_staging_table_name = self._send_primary_need_staging_table_name(context)
        home_language_staging_table_name = self._home_language_staging_table_name(context)
        ethnicity_columns_sql = ",\n                                ".join(
            [*_ETHNICITY_PERCENTAGE_COLUMNS, *_ETHNICITY_COUNT_COLUMNS]
        )
        ethnicity_selected_columns_sql = ",\n                                ".join(
            [
                f"staged.{column}"
                for column in [*_ETHNICITY_PERCENTAGE_COLUMNS, *_ETHNICITY_COUNT_COLUMNS]
            ]
        )
        ethnicity_update_columns_sql = ",\n                                ".join(
            [
                *(f"{column} = EXCLUDED.{column}" for column in _ETHNICITY_PERCENTAGE_COLUMNS),
                *(f"{column} = EXCLUDED.{column}" for column in _ETHNICITY_COUNT_COLUMNS),
                "source_dataset_id = EXCLUDED.source_dataset_id",
                "source_dataset_version = EXCLUDED.source_dataset_version",
                "updated_at = timezone('utc', now())",
            ]
        )
        with self._engine.begin() as connection:
            promoted_rows = int(
                connection.execute(
                    text(
                        f"""
                        WITH upserted AS (
                            INSERT INTO school_demographics_yearly (
                                urn,
                                academic_year,
                                disadvantaged_pct,
                                fsm_pct,
                                fsm6_pct,
                                sen_pct,
                                sen_support_pct,
                                ehcp_pct,
                                eal_pct,
                                first_language_english_pct,
                                first_language_unclassified_pct,
                                male_pct,
                                female_pct,
                                pupil_mobility_pct,
                                total_pupils,
                                has_fsm6_data,
                                has_gender_data,
                                has_mobility_data,
                                has_ethnicity_data,
                                has_top_languages_data,
                                has_send_primary_need_data,
                                source_dataset_id,
                                source_dataset_version,
                                updated_at
                            )
                            SELECT
                                staged.urn,
                                staged.academic_year,
                                staged.disadvantaged_pct,
                                staged.fsm_pct,
                                staged.fsm6_pct,
                                staged.sen_pct,
                                staged.sen_support_pct,
                                staged.ehcp_pct,
                                staged.eal_pct,
                                staged.first_language_english_pct,
                                staged.first_language_unclassified_pct,
                                staged.male_pct,
                                staged.female_pct,
                                staged.pupil_mobility_pct,
                                staged.total_pupils,
                                staged.has_fsm6_data,
                                staged.has_gender_data,
                                staged.has_mobility_data,
                                staged.has_ethnicity_data,
                                staged.has_top_languages_data,
                                staged.has_send_primary_need_data,
                                staged.source_dataset_id,
                                staged.source_dataset_version,
                                timezone('utc', now())
                            FROM staging.{staging_table_name} AS staged
                            INNER JOIN schools ON schools.urn = staged.urn
                            ON CONFLICT (urn, academic_year) DO UPDATE SET
                                disadvantaged_pct = EXCLUDED.disadvantaged_pct,
                                fsm_pct = EXCLUDED.fsm_pct,
                                fsm6_pct = EXCLUDED.fsm6_pct,
                                sen_pct = EXCLUDED.sen_pct,
                                sen_support_pct = EXCLUDED.sen_support_pct,
                                ehcp_pct = EXCLUDED.ehcp_pct,
                                eal_pct = EXCLUDED.eal_pct,
                                first_language_english_pct = EXCLUDED.first_language_english_pct,
                                first_language_unclassified_pct = EXCLUDED.first_language_unclassified_pct,
                                male_pct = EXCLUDED.male_pct,
                                female_pct = EXCLUDED.female_pct,
                                pupil_mobility_pct = EXCLUDED.pupil_mobility_pct,
                                total_pupils = EXCLUDED.total_pupils,
                                has_fsm6_data = EXCLUDED.has_fsm6_data,
                                has_gender_data = EXCLUDED.has_gender_data,
                                has_mobility_data = EXCLUDED.has_mobility_data,
                                has_ethnicity_data = EXCLUDED.has_ethnicity_data,
                                has_top_languages_data = EXCLUDED.has_top_languages_data,
                                has_send_primary_need_data = EXCLUDED.has_send_primary_need_data,
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
            connection.execute(
                text(
                    f"""
                    INSERT INTO school_ethnicity_yearly (
                        urn,
                        academic_year,
                        {ethnicity_columns_sql},
                        source_dataset_id,
                        source_dataset_version,
                        updated_at
                    )
                    SELECT
                        staged.urn,
                        staged.academic_year,
                        {ethnicity_selected_columns_sql},
                        staged.source_dataset_id,
                        staged.source_dataset_version,
                        timezone('utc', now())
                    FROM staging.{ethnicity_staging_table_name} AS staged
                    INNER JOIN schools ON schools.urn = staged.urn
                    ON CONFLICT (urn, academic_year) DO UPDATE SET
                        {ethnicity_update_columns_sql}
                    """
                )
            )
            connection.execute(
                text(
                    f"""
                    INSERT INTO school_send_primary_need_yearly (
                        urn,
                        academic_year,
                        need_key,
                        need_label,
                        pupil_count,
                        percentage,
                        source_dataset_id,
                        source_dataset_version,
                        updated_at
                    )
                    SELECT
                        staged.urn,
                        staged.academic_year,
                        staged.need_key,
                        staged.need_label,
                        staged.pupil_count,
                        staged.percentage,
                        staged.source_dataset_id,
                        staged.source_dataset_version,
                        timezone('utc', now())
                    FROM staging.{send_primary_need_staging_table_name} AS staged
                    INNER JOIN schools ON schools.urn = staged.urn
                    ON CONFLICT (urn, academic_year, need_key) DO UPDATE SET
                        need_label = EXCLUDED.need_label,
                        pupil_count = EXCLUDED.pupil_count,
                        percentage = EXCLUDED.percentage,
                        source_dataset_id = EXCLUDED.source_dataset_id,
                        source_dataset_version = EXCLUDED.source_dataset_version,
                        updated_at = timezone('utc', now())
                    """
                )
            )
            connection.execute(
                text(
                    f"""
                    INSERT INTO school_home_language_yearly (
                        urn,
                        academic_year,
                        language_key,
                        language_label,
                        rank,
                        pupil_count,
                        percentage,
                        source_dataset_id,
                        source_dataset_version,
                        updated_at
                    )
                    SELECT
                        staged.urn,
                        staged.academic_year,
                        staged.language_key,
                        staged.language_label,
                        staged.rank,
                        staged.pupil_count,
                        staged.percentage,
                        staged.source_dataset_id,
                        staged.source_dataset_version,
                        timezone('utc', now())
                    FROM staging.{home_language_staging_table_name} AS staged
                    INNER JOIN schools ON schools.urn = staged.urn
                    ON CONFLICT (urn, academic_year, language_key) DO UPDATE SET
                        language_label = EXCLUDED.language_label,
                        rank = EXCLUDED.rank,
                        pupil_count = EXCLUDED.pupil_count,
                        percentage = EXCLUDED.percentage,
                        source_dataset_id = EXCLUDED.source_dataset_id,
                        source_dataset_version = EXCLUDED.source_dataset_version,
                        updated_at = timezone('utc', now())
                    """
                )
            )
            connection.execute(
                text(
                    f"""
                    DELETE FROM school_ethnicity_yearly AS target
                    USING staging.{staging_table_name} AS staged
                    WHERE
                        target.urn = staged.urn
                        AND target.academic_year = staged.academic_year
                        AND staged.has_ethnicity_data = FALSE
                    """
                )
            )
            connection.execute(
                text(
                    f"""
                    DELETE FROM school_send_primary_need_yearly AS target
                    USING staging.{staging_table_name} AS staged
                    WHERE
                        target.urn = staged.urn
                        AND target.academic_year = staged.academic_year
                        AND NOT EXISTS (
                            SELECT 1
                            FROM staging.{send_primary_need_staging_table_name} AS source_rows
                            WHERE
                                source_rows.urn = target.urn
                                AND source_rows.academic_year = target.academic_year
                                AND source_rows.need_key = target.need_key
                        )
                    """
                )
            )
            connection.execute(
                text(
                    f"""
                    DELETE FROM school_home_language_yearly AS target
                    USING staging.{staging_table_name} AS staged
                    WHERE
                        target.urn = staged.urn
                        AND target.academic_year = staged.academic_year
                        AND NOT EXISTS (
                            SELECT 1
                            FROM staging.{home_language_staging_table_name} AS source_rows
                            WHERE
                                source_rows.urn = target.urn
                                AND source_rows.academic_year = target.academic_year
                                AND source_rows.language_key = target.language_key
                        )
                    """
                )
            )
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{ethnicity_staging_table_name}"))
            connection.execute(
                text(f"DROP TABLE IF EXISTS staging.{send_primary_need_staging_table_name}")
            )
            connection.execute(
                text(f"DROP TABLE IF EXISTS staging.{home_language_staging_table_name}")
            )

        return promoted_rows

    def _discover_release_files(self) -> tuple[ReleaseFileDescriptor, ...]:
        release_slugs = self._selected_release_slugs()
        descriptors: list[ReleaseFileDescriptor] = []

        descriptor_specs = (
            (DemographicsSourceFamily.SPC, self._spc_publication_slug),
            (DemographicsSourceFamily.SEN, self._sen_publication_slug),
        )

        for family, publication_slug in descriptor_specs:
            for release_slug in release_slugs:
                try:
                    descriptors.append(
                        self._discover_release_file(
                            family=family,
                            publication_slug=publication_slug,
                            release_slug=release_slug,
                        )
                    )
                except ValueError:
                    if self._strict_mode:
                        raise

        return tuple(
            sorted(
                descriptors,
                key=lambda descriptor: (
                    descriptor.family.value,
                    descriptor.release_slug,
                    descriptor.file_id,
                ),
            )
        )

    def _selected_release_slugs(self) -> tuple[str, ...]:
        sorted_unique = tuple(dict.fromkeys(self._release_slugs))
        return sorted_unique[-self._lookback_years :]

    def _discover_release_file(
        self,
        *,
        family: DemographicsSourceFamily,
        publication_slug: str,
        release_slug: str,
    ) -> ReleaseFileDescriptor:
        page_url = build_release_page_url(
            publication_slug=publication_slug,
            release_slug=release_slug,
        )
        html = self._fetch_text(page_url)
        release_version = parse_release_version_from_page(html)

        release_version_id_raw = release_version.get("id")
        if not isinstance(release_version_id_raw, str) or not release_version_id_raw.strip():
            raise ValueError(
                f"Release page is missing release version id for {publication_slug}/{release_slug}."
            )
        release_version_id = release_version_id_raw.strip()

        download_files = release_version.get("downloadFiles")
        if not isinstance(download_files, list):
            raise ValueError(
                f"Release page is missing downloadFiles for {publication_slug}/{release_slug}."
            )

        selected = select_school_level_file(download_files)
        if selected is None:
            raise ValueError(
                f"No school-level underlying data file found for {publication_slug}/{release_slug}."
            )

        file_id_raw = selected.get("id")
        file_name_raw = selected.get("name")
        if not isinstance(file_id_raw, str) or not file_id_raw.strip():
            raise ValueError(
                f"Selected release file has no id for {publication_slug}/{release_slug}."
            )
        if not isinstance(file_name_raw, str) or not file_name_raw.strip():
            raise ValueError(
                f"Selected release file has no name for {publication_slug}/{release_slug}."
            )

        return ReleaseFileDescriptor(
            family=family,
            publication_slug=publication_slug,
            release_slug=release_slug,
            release_version_id=release_version_id,
            file_id=file_id_raw.strip(),
            file_name=file_name_raw.strip(),
        )

    @staticmethod
    def _staging_table_name(context: PipelineRunContext) -> str:
        return f"dfe_characteristics__{context.run_id.hex}"

    @staticmethod
    def _ethnicity_staging_table_name(context: PipelineRunContext) -> str:
        return f"dfe_characteristics_ethnicity__{context.run_id.hex}"

    @staticmethod
    def _send_primary_need_staging_table_name(context: PipelineRunContext) -> str:
        return f"dfe_characteristics_send_need__{context.run_id.hex}"

    @staticmethod
    def _home_language_staging_table_name(context: PipelineRunContext) -> str:
        return f"dfe_characteristics_home_lang__{context.run_id.hex}"


def build_release_page_url(*, publication_slug: str, release_slug: str) -> str:
    return RELEASE_PAGE_URL_TEMPLATE.format(
        publication_slug=publication_slug,
        release_slug=release_slug,
    )


def parse_release_version_from_page(html: str) -> dict[str, object]:
    next_data_payload = parse_next_data_payload(html)
    props_payload = next_data_payload.get("props")
    if not isinstance(props_payload, dict):
        raise ValueError("Release page does not contain props payload.")

    page_props_payload = props_payload.get("pageProps")
    if not isinstance(page_props_payload, dict):
        raise ValueError("Release page does not contain pageProps payload.")

    release_version = page_props_payload.get("releaseVersion")
    if isinstance(release_version, dict):
        return release_version
    raise ValueError("Release page does not contain releaseVersion payload.")


def parse_next_data_payload(html: str) -> dict[str, object]:
    match = _NEXT_DATA_PATTERN.search(html)
    if match is None:
        raise ValueError("Release page HTML does not contain __NEXT_DATA__ payload.")

    try:
        payload = json.loads(match.group("payload"))
    except json.JSONDecodeError as exc:
        raise ValueError("Release page __NEXT_DATA__ payload is invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Release page __NEXT_DATA__ payload was not an object.")

    return payload


def select_school_level_file(download_files: Sequence[object]) -> dict[str, object] | None:
    candidates: list[dict[str, object]] = []
    for item in download_files:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        normalized_name = name.casefold()
        if _SCHOOL_LEVEL_FILE_NAME_TOKEN not in normalized_name:
            continue
        if _CLASS_SIZE_FILE_NAME_TOKEN in normalized_name:
            continue
        candidates.append(item)

    if not candidates:
        return None

    candidates.sort(key=lambda item: str(item.get("id") or ""))
    return candidates[0]


def _merge_rows(
    *,
    spc_rows: Mapping[tuple[str, str], _SpcRecord],
    sen_rows: Mapping[tuple[str, str], _SenRecord],
) -> tuple[
    list[_MergedRecord],
    list[_EthnicityRecord],
    list[_SendPrimaryNeedRecord],
    list[_HomeLanguageRecord],
]:
    merged: list[_MergedRecord] = []
    ethnicity_rows: list[_EthnicityRecord] = []
    send_primary_need_rows: list[_SendPrimaryNeedRecord] = []
    home_language_rows: list[_HomeLanguageRecord] = []
    keys = sorted(set(spc_rows.keys()) | set(sen_rows.keys()))
    for key in keys:
        spc_row = spc_rows.get(key)
        sen_row = sen_rows.get(key)

        source_dataset_tokens: list[str] = []
        source_dataset_version_tokens: list[str] = []
        if spc_row is not None:
            source_dataset_tokens.append(f"spc:{spc_row.release_version_id}")
            source_dataset_version_tokens.append(f"spc:{spc_row.file_id}")
        if sen_row is not None:
            source_dataset_tokens.append(f"sen:{sen_row.release_version_id}")
            source_dataset_version_tokens.append(f"sen:{sen_row.file_id}")

        merged.append(
            _MergedRecord(
                urn=key[0],
                academic_year=key[1],
                fsm_pct=spc_row.fsm_pct if spc_row is not None else None,
                fsm6_pct=spc_row.fsm6_pct if spc_row is not None else None,
                disadvantaged_pct=spc_row.disadvantaged_pct if spc_row is not None else None,
                sen_pct=sen_row.sen_support_pct if sen_row is not None else None,
                sen_support_pct=sen_row.sen_support_pct if sen_row is not None else None,
                ehcp_pct=sen_row.ehcp_pct if sen_row is not None else None,
                eal_pct=spc_row.eal_pct if spc_row is not None else None,
                first_language_english_pct=(
                    spc_row.first_language_english_pct if spc_row is not None else None
                ),
                first_language_unclassified_pct=(
                    spc_row.first_language_unclassified_pct if spc_row is not None else None
                ),
                male_pct=spc_row.male_pct if spc_row is not None else None,
                female_pct=spc_row.female_pct if spc_row is not None else None,
                pupil_mobility_pct=spc_row.pupil_mobility_pct if spc_row is not None else None,
                total_pupils=sen_row.total_pupils if sen_row is not None else None,
                has_fsm6_data=spc_row.has_fsm6_data if spc_row is not None else False,
                has_gender_data=spc_row.has_gender_data if spc_row is not None else False,
                has_mobility_data=spc_row.has_mobility_data if spc_row is not None else False,
                has_ethnicity_data=(spc_row.has_ethnicity_data if spc_row is not None else False),
                has_top_languages_data=(
                    spc_row.has_top_languages_data if spc_row is not None else False
                ),
                has_send_primary_need_data=(
                    sen_row.has_primary_need_data if sen_row is not None else False
                ),
                source_dataset_id="|".join(source_dataset_tokens),
                source_dataset_version=(
                    "|".join(source_dataset_version_tokens)
                    if source_dataset_version_tokens
                    else None
                ),
            )
        )
        if spc_row is not None and spc_row.has_ethnicity_data:
            ethnicity_rows.append(
                _EthnicityRecord(
                    urn=spc_row.urn,
                    academic_year=spc_row.academic_year,
                    percentages=dict(spc_row.ethnicity_percentages),
                    counts=dict(spc_row.ethnicity_counts),
                    source_dataset_id=f"spc:{spc_row.release_version_id}",
                    source_dataset_version=f"spc:{spc_row.file_id}",
                )
            )
        if sen_row is not None and sen_row.primary_needs:
            for need in sen_row.primary_needs:
                send_primary_need_rows.append(
                    _SendPrimaryNeedRecord(
                        urn=sen_row.urn,
                        academic_year=sen_row.academic_year,
                        need_key=need["key"],
                        need_label=need["label"],
                        pupil_count=need["count"],
                        percentage=need["percentage"],
                        source_dataset_id=f"sen:{sen_row.release_version_id}",
                        source_dataset_version=f"sen:{sen_row.file_id}",
                    )
                )

        if spc_row is not None and spc_row.top_home_languages:
            for rank, language in enumerate(spc_row.top_home_languages, start=1):
                home_language_rows.append(
                    _HomeLanguageRecord(
                        urn=spc_row.urn,
                        academic_year=spc_row.academic_year,
                        language_key=language["key"],
                        language_label=language["label"],
                        rank=rank,
                        pupil_count=language["count"],
                        percentage=language["percentage"],
                        source_dataset_id=f"spc:{spc_row.release_version_id}",
                        source_dataset_version=f"spc:{spc_row.file_id}",
                    )
                )

    return merged, ethnicity_rows, send_primary_need_rows, home_language_rows


def _build_bronze_file_name(descriptor: ReleaseFileDescriptor) -> str:
    release_slug_token = descriptor.release_slug.replace("-", "_")
    return f"{descriptor.family.value}_{release_slug_token}_{descriptor.file_id}.csv"


def _load_manifest_assets(manifest_path: Path) -> tuple[BronzeManifestAsset, ...]:
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

    assets: list[BronzeManifestAsset] = []
    for item in assets_payload:
        if not isinstance(item, dict):
            continue

        family_raw = item.get("family")
        publication_slug = item.get("publication_slug")
        release_slug = item.get("release_slug")
        release_version_id = item.get("release_version_id")
        file_id = item.get("file_id")
        file_name = item.get("file_name")
        bronze_file_name = item.get("bronze_file_name")
        downloaded_at = item.get("downloaded_at")
        sha256 = item.get("sha256")
        row_count = item.get("row_count")

        try:
            family = DemographicsSourceFamily(str(family_raw))
        except ValueError:
            continue

        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                publication_slug,
                release_slug,
                release_version_id,
                file_id,
                file_name,
                bronze_file_name,
                downloaded_at,
                sha256,
            )
        ):
            continue

        if not isinstance(row_count, int):
            if isinstance(row_count, float) or (isinstance(row_count, str) and row_count.isdigit()):
                row_count = int(row_count)
            else:
                continue

        assets.append(
            BronzeManifestAsset(
                family=family,
                publication_slug=str(publication_slug).strip(),
                release_slug=str(release_slug).strip(),
                release_version_id=str(release_version_id).strip(),
                file_id=str(file_id).strip(),
                file_name=str(file_name).strip(),
                bronze_file_name=str(bronze_file_name).strip(),
                downloaded_at=str(downloaded_at).strip(),
                sha256=str(sha256).strip(),
                row_count=int(row_count),
            )
        )

    return tuple(
        sorted(
            assets,
            key=lambda asset: (
                asset.family.value,
                asset.release_slug,
                asset.file_id,
            ),
        )
    )


def _normalize_release_slug(value: str) -> str:
    normalized = value.strip()
    if not re.match(r"^\d{4}-\d{2}$", normalized):
        raise ValueError(f"Invalid release slug '{value}'.")
    return normalized


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
        return max(0, sum(1 for _ in csv.reader(file_handle)) - 1)


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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
