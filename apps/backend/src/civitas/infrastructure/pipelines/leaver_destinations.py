from __future__ import annotations

import csv
import hashlib
import json
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import leaver_destinations as destinations_contract

BRONZE_MANIFEST_FILE_NAME = "leaver_destinations.manifest.json"


@dataclass(frozen=True)
class _DownloadSpec:
    destination_stage: destinations_contract.DestinationStage
    release_page_url: str
    data_catalogue_url: str
    public_csv_route_url: str
    source_reference: str


@dataclass(frozen=True)
class _DownloadedAsset:
    destination_stage: destinations_contract.DestinationStage
    destination_year: str
    release_page_url: str
    data_catalogue_url: str
    public_csv_route_url: str
    source_reference: str
    observed_http_status: int | None
    observed_content_type: str | None
    observed_content_disposition: str | None
    observed_middleware_rewrite: str | None
    downloaded_at_utc: str
    bronze_file_name: str
    bronze_relative_path: str
    sha256: str
    row_count: int
    header_count: int
    headers: tuple[str, ...]


@dataclass(frozen=True)
class _DownloadedPayload:
    source_reference: str
    body: bytes
    observed_http_status: int | None
    observed_content_type: str | None
    observed_content_disposition: str | None
    observed_middleware_rewrite: str | None


@dataclass(frozen=True)
class _StagedRow:
    academic_year: str
    destination_stage: destinations_contract.DestinationStage
    school_urn: str
    school_laestab: str | None
    school_name: str
    admission_policy: str | None
    entry_gender: str | None
    institution_group: str | None
    institution_type: str | None
    qualification_group: str
    qualification_level: str
    breakdown_topic: str
    breakdown: str
    data_type: destinations_contract.DestinationDataType
    cohort_count: int | None
    overall_value: float | None
    education_value: float | None
    apprenticeship_value: float | None
    employment_value: float | None
    not_sustained_value: float | None
    activity_unknown_value: float | None
    fe_value: float | None
    other_education_value: float | None
    school_sixth_form_value: float | None
    sixth_form_college_value: float | None
    higher_education_value: float | None
    source_file_url: str
    source_updated_at_utc: datetime


@dataclass(frozen=True)
class _SchoolJoinRow:
    urn: str
    school_laestab: str | None


class LeaverDestinationsPipeline:
    source = PipelineSource.LEAVER_DESTINATIONS

    def __init__(
        self,
        engine: Engine | None,
        *,
        ks4_source_csv: str | None = None,
        ks4_source_url: str,
        ks4_release_page_url: str,
        ks4_data_catalogue_url: str,
        study_16_to_18_source_csv: str | None = None,
        study_16_to_18_source_url: str,
        study_16_to_18_release_page_url: str,
        study_16_to_18_data_catalogue_url: str,
    ) -> None:
        self._engine = engine
        self._download_specs = (
            _DownloadSpec(
                destination_stage="ks4",
                release_page_url=ks4_release_page_url,
                data_catalogue_url=ks4_data_catalogue_url,
                public_csv_route_url=ks4_source_url,
                source_reference=ks4_source_csv or ks4_source_url,
            ),
            _DownloadSpec(
                destination_stage="16_to_18",
                release_page_url=study_16_to_18_release_page_url,
                data_catalogue_url=study_16_to_18_data_catalogue_url,
                public_csv_route_url=study_16_to_18_source_url,
                source_reference=study_16_to_18_source_csv or study_16_to_18_source_url,
            ),
        )

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        downloaded_assets: list[_DownloadedAsset] = []
        total_rows = 0
        for spec in self._download_specs:
            payload = _download_payload(
                source_reference=spec.source_reference,
                timeout_seconds=context.http_timeout_seconds,
            )
            (
                destination_year,
                bronze_file_name,
                row_count,
                headers,
            ) = _inspect_downloaded_csv(
                body=payload.body,
                destination_stage=spec.destination_stage,
                observed_file_name=payload.observed_content_disposition,
            )
            asset_directory = context.bronze_source_path / spec.destination_stage / destination_year
            asset_directory.mkdir(parents=True, exist_ok=True)
            target_csv = asset_directory / bronze_file_name
            target_csv.write_bytes(payload.body)

            asset = _DownloadedAsset(
                destination_stage=spec.destination_stage,
                destination_year=destination_year,
                release_page_url=spec.release_page_url,
                data_catalogue_url=spec.data_catalogue_url,
                public_csv_route_url=spec.public_csv_route_url,
                source_reference=payload.source_reference,
                observed_http_status=payload.observed_http_status,
                observed_content_type=payload.observed_content_type,
                observed_content_disposition=payload.observed_content_disposition,
                observed_middleware_rewrite=payload.observed_middleware_rewrite,
                downloaded_at_utc=datetime.now(timezone.utc).isoformat(),
                bronze_file_name=bronze_file_name,
                bronze_relative_path=target_csv.relative_to(context.bronze_source_path).as_posix(),
                sha256=_sha256_bytes(payload.body),
                row_count=row_count,
                header_count=len(headers),
                headers=headers,
            )
            _write_asset_manifest(asset_directory / "manifest.json", asset)
            downloaded_assets.append(asset)
            total_rows += row_count

        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
        manifest_path.write_text(
            json.dumps(
                {
                    "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                    "normalization_contract_version": destinations_contract.CONTRACT_VERSION,
                    "assets": [_asset_to_manifest_record(asset) for asset in downloaded_assets],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return total_rows

    def stage(self, context: PipelineRunContext) -> StageResult:
        if self._engine is None:
            raise ValueError("Pipeline engine is required for stage.")

        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
        manifest_assets = _load_manifest_assets(manifest_path)
        if not manifest_assets:
            raise FileNotFoundError("Leaver destinations manifest is missing; run download first.")

        rows_by_stage_and_key: dict[
            tuple[destinations_contract.DestinationStage, tuple[str, ...]],
            _StagedRow,
        ] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []

        for asset in manifest_assets:
            csv_path = context.bronze_source_path / asset.bronze_relative_path
            if not csv_path.exists():
                raise FileNotFoundError(
                    f"Leaver destinations bronze file not found at '{csv_path}'."
                )
            with csv_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
                reader = csv.DictReader(file_handle)
                if reader.fieldnames is None:
                    raise ValueError(f"Leaver destinations CSV '{csv_path}' has no header row.")
                destinations_contract.validate_headers(
                    destination_stage=asset.destination_stage,
                    headers=tuple(reader.fieldnames),
                )
                for raw_row in reader:
                    normalized_row, rejection = destinations_contract.normalize_row(
                        raw_row,
                        destination_stage=asset.destination_stage,
                        source_file_url=asset.source_reference,
                    )
                    if normalized_row is None:
                        if rejection is not None:
                            rejected_rows.append((rejection, dict(raw_row)))
                        continue
                    staged_row = _StagedRow(
                        academic_year=normalized_row["academic_year"],
                        destination_stage=normalized_row["destination_stage"],
                        school_urn=normalized_row["school_urn"],
                        school_laestab=normalized_row["school_laestab"],
                        school_name=normalized_row["school_name"],
                        admission_policy=normalized_row["admission_policy"],
                        entry_gender=normalized_row["entry_gender"],
                        institution_group=normalized_row["institution_group"],
                        institution_type=normalized_row["institution_type"],
                        qualification_group=normalized_row["qualification_group"] or "",
                        qualification_level=normalized_row["qualification_level"] or "",
                        breakdown_topic=normalized_row["breakdown_topic"],
                        breakdown=normalized_row["breakdown"],
                        data_type=normalized_row["data_type"],
                        cohort_count=normalized_row["cohort_count"],
                        overall_value=normalized_row["overall_value"],
                        education_value=normalized_row["education_value"],
                        apprenticeship_value=normalized_row["apprenticeship_value"],
                        employment_value=normalized_row["employment_value"],
                        not_sustained_value=normalized_row["not_sustained_value"],
                        activity_unknown_value=normalized_row["activity_unknown_value"],
                        fe_value=normalized_row["fe_value"],
                        other_education_value=normalized_row["other_education_value"],
                        school_sixth_form_value=normalized_row["school_sixth_form_value"],
                        sixth_form_college_value=normalized_row["sixth_form_college_value"],
                        higher_education_value=normalized_row["higher_education_value"],
                        source_file_url=normalized_row["source_file_url"],
                        source_updated_at_utc=_parse_datetime(asset.downloaded_at_utc),
                    )
                    row_key = (
                        staged_row.academic_year,
                        staged_row.school_urn,
                        staged_row.school_laestab or "",
                        staged_row.qualification_group,
                        staged_row.qualification_level,
                        staged_row.breakdown_topic,
                        staged_row.breakdown,
                        staged_row.data_type,
                    )
                    rows_by_stage_and_key[(staged_row.destination_stage, row_key)] = staged_row

        ks4_rows = _sorted_staged_rows(rows_by_stage_and_key, destination_stage="ks4")
        study_rows = _sorted_staged_rows(rows_by_stage_and_key, destination_stage="16_to_18")
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            self._recreate_stage_table(
                connection,
                table_name=self._staging_table_name(context, destination_stage="ks4"),
            )
            self._recreate_stage_table(
                connection,
                table_name=self._staging_table_name(context, destination_stage="16_to_18"),
            )
            if ks4_rows:
                self._insert_stage_rows(
                    connection,
                    context=context,
                    table_name=self._staging_table_name(context, destination_stage="ks4"),
                    rows=ks4_rows,
                )
            if study_rows:
                self._insert_stage_rows(
                    connection,
                    context=context,
                    table_name=self._staging_table_name(context, destination_stage="16_to_18"),
                    rows=study_rows,
                )
            if rejected_rows:
                _insert_rejections(
                    connection,
                    context=context,
                    stage="stage",
                    rejected_rows=rejected_rows,
                )

        return StageResult(
            staged_rows=len(ks4_rows) + len(study_rows),
            rejected_rows=len(rejected_rows),
            contract_version=destinations_contract.CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        if self._engine is None:
            raise ValueError("Pipeline engine is required for promote.")

        with self._engine.begin() as connection:
            ks4_rows = tuple(
                connection.execute(
                    text(
                        f"SELECT * FROM staging.{self._staging_table_name(context, destination_stage='ks4')}"
                    )
                ).mappings()
            )
            study_rows = tuple(
                connection.execute(
                    text(
                        f"SELECT * FROM staging.{self._staging_table_name(context, destination_stage='16_to_18')}"
                    )
                ).mappings()
            )
            school_rows = tuple(
                connection.execute(
                    text(
                        """
                        SELECT urn, school_laestab
                        FROM schools
                        """
                    )
                ).mappings()
            )
            school_by_urn = {
                str(row["urn"]): _SchoolJoinRow(
                    urn=str(row["urn"]),
                    school_laestab=_to_optional_str(row["school_laestab"]),
                )
                for row in school_rows
            }
            schools_by_laestab: dict[str, list[_SchoolJoinRow]] = {}
            for row in school_by_urn.values():
                if row.school_laestab is None:
                    continue
                schools_by_laestab.setdefault(row.school_laestab, []).append(row)

            grouped_rows: dict[
                tuple[str, str, str, str, str, str, str], list[Mapping[str, Any]]
            ] = {}
            rejected_rows: list[tuple[str, dict[str, Any]]] = []
            for staged_row_record in (*ks4_rows, *study_rows):
                staged_row = dict(staged_row_record)
                resolved_urn, rejection = _resolve_school_urn(
                    staged_row=staged_row,
                    school_by_urn=school_by_urn,
                    schools_by_laestab=schools_by_laestab,
                )
                if resolved_urn is None:
                    rejected_rows.append((rejection or "school_not_found", staged_row))
                    continue
                grouped_rows.setdefault(
                    (
                        resolved_urn,
                        str(staged_row["academic_year"]),
                        str(staged_row["destination_stage"]),
                        _to_optional_str(staged_row.get("qualification_group")) or "",
                        _to_optional_str(staged_row.get("qualification_level")) or "",
                        str(staged_row["breakdown_topic"]),
                        str(staged_row["breakdown"]),
                    ),
                    [],
                ).append(staged_row)

            aggregated_rows = [
                _aggregate_group_rows(
                    urn=urn,
                    academic_year=academic_year,
                    destination_stage=destination_stage,
                    qualification_group=qualification_group,
                    qualification_level=qualification_level,
                    breakdown_topic=breakdown_topic,
                    breakdown=breakdown,
                    rows=rows,
                )
                for (
                    urn,
                    academic_year,
                    destination_stage,
                    qualification_group,
                    qualification_level,
                    breakdown_topic,
                    breakdown,
                ), rows in sorted(grouped_rows.items())
            ]
            if rejected_rows:
                _insert_rejections(
                    connection,
                    context=context,
                    stage="promote",
                    rejected_rows=rejected_rows,
                )

            promoted_rows = 0
            if aggregated_rows:
                upsert = text(
                    """
                    INSERT INTO school_leaver_destinations_yearly (
                        urn,
                        academic_year,
                        destination_stage,
                        qualification_group,
                        qualification_level,
                        breakdown_topic,
                        breakdown,
                        school_name,
                        school_laestab,
                        admission_policy,
                        entry_gender,
                        institution_group,
                        institution_type,
                        cohort_count,
                        overall_count,
                        overall_pct,
                        education_count,
                        education_pct,
                        apprenticeship_count,
                        apprenticeship_pct,
                        employment_count,
                        employment_pct,
                        not_sustained_count,
                        not_sustained_pct,
                        activity_unknown_count,
                        activity_unknown_pct,
                        fe_count,
                        fe_pct,
                        other_education_count,
                        other_education_pct,
                        school_sixth_form_count,
                        school_sixth_form_pct,
                        sixth_form_college_count,
                        sixth_form_college_pct,
                        higher_education_count,
                        higher_education_pct,
                        source_file_url,
                        source_updated_at_utc,
                        updated_at
                    ) VALUES (
                        :urn,
                        :academic_year,
                        :destination_stage,
                        :qualification_group,
                        :qualification_level,
                        :breakdown_topic,
                        :breakdown,
                        :school_name,
                        :school_laestab,
                        :admission_policy,
                        :entry_gender,
                        :institution_group,
                        :institution_type,
                        :cohort_count,
                        :overall_count,
                        :overall_pct,
                        :education_count,
                        :education_pct,
                        :apprenticeship_count,
                        :apprenticeship_pct,
                        :employment_count,
                        :employment_pct,
                        :not_sustained_count,
                        :not_sustained_pct,
                        :activity_unknown_count,
                        :activity_unknown_pct,
                        :fe_count,
                        :fe_pct,
                        :other_education_count,
                        :other_education_pct,
                        :school_sixth_form_count,
                        :school_sixth_form_pct,
                        :sixth_form_college_count,
                        :sixth_form_college_pct,
                        :higher_education_count,
                        :higher_education_pct,
                        :source_file_url,
                        :source_updated_at_utc,
                        timezone('utc', now())
                    )
                    ON CONFLICT (
                        urn,
                        academic_year,
                        destination_stage,
                        qualification_group,
                        qualification_level,
                        breakdown_topic,
                        breakdown
                    ) DO UPDATE SET
                        school_name = EXCLUDED.school_name,
                        school_laestab = EXCLUDED.school_laestab,
                        admission_policy = EXCLUDED.admission_policy,
                        entry_gender = EXCLUDED.entry_gender,
                        institution_group = EXCLUDED.institution_group,
                        institution_type = EXCLUDED.institution_type,
                        cohort_count = EXCLUDED.cohort_count,
                        overall_count = EXCLUDED.overall_count,
                        overall_pct = EXCLUDED.overall_pct,
                        education_count = EXCLUDED.education_count,
                        education_pct = EXCLUDED.education_pct,
                        apprenticeship_count = EXCLUDED.apprenticeship_count,
                        apprenticeship_pct = EXCLUDED.apprenticeship_pct,
                        employment_count = EXCLUDED.employment_count,
                        employment_pct = EXCLUDED.employment_pct,
                        not_sustained_count = EXCLUDED.not_sustained_count,
                        not_sustained_pct = EXCLUDED.not_sustained_pct,
                        activity_unknown_count = EXCLUDED.activity_unknown_count,
                        activity_unknown_pct = EXCLUDED.activity_unknown_pct,
                        fe_count = EXCLUDED.fe_count,
                        fe_pct = EXCLUDED.fe_pct,
                        other_education_count = EXCLUDED.other_education_count,
                        other_education_pct = EXCLUDED.other_education_pct,
                        school_sixth_form_count = EXCLUDED.school_sixth_form_count,
                        school_sixth_form_pct = EXCLUDED.school_sixth_form_pct,
                        sixth_form_college_count = EXCLUDED.sixth_form_college_count,
                        sixth_form_college_pct = EXCLUDED.sixth_form_college_pct,
                        higher_education_count = EXCLUDED.higher_education_count,
                        higher_education_pct = EXCLUDED.higher_education_pct,
                        source_file_url = EXCLUDED.source_file_url,
                        source_updated_at_utc = EXCLUDED.source_updated_at_utc,
                        updated_at = timezone('utc', now())
                    """
                )
                for chunk in chunked(aggregated_rows, context.promote_chunk_size):
                    result = connection.execute(upsert, chunk)
                    promoted_rows += int(result.rowcount or 0)

            connection.execute(
                text(
                    f"DROP TABLE IF EXISTS staging.{self._staging_table_name(context, destination_stage='ks4')}"
                )
            )
            connection.execute(
                text(
                    f"DROP TABLE IF EXISTS staging.{self._staging_table_name(context, destination_stage='16_to_18')}"
                )
            )
        return promoted_rows

    def _recreate_stage_table(self, connection, *, table_name: str) -> None:
        connection.execute(text(f"DROP TABLE IF EXISTS staging.{table_name}"))
        connection.execute(
            text(
                f"""
                CREATE TABLE staging.{table_name} (
                    academic_year text NOT NULL,
                    destination_stage text NOT NULL,
                    school_urn text NOT NULL,
                    school_laestab text NULL,
                    school_name text NOT NULL,
                    admission_policy text NULL,
                    entry_gender text NULL,
                    institution_group text NULL,
                    institution_type text NULL,
                    qualification_group text NOT NULL,
                    qualification_level text NOT NULL,
                    breakdown_topic text NOT NULL,
                    breakdown text NOT NULL,
                    data_type text NOT NULL,
                    cohort_count integer NULL,
                    overall_value double precision NULL,
                    education_value double precision NULL,
                    apprenticeship_value double precision NULL,
                    employment_value double precision NULL,
                    not_sustained_value double precision NULL,
                    activity_unknown_value double precision NULL,
                    fe_value double precision NULL,
                    other_education_value double precision NULL,
                    school_sixth_form_value double precision NULL,
                    sixth_form_college_value double precision NULL,
                    higher_education_value double precision NULL,
                    source_file_url text NOT NULL,
                    source_updated_at_utc timestamptz NOT NULL
                )
                """
            )
        )

    def _insert_stage_rows(
        self,
        connection,
        *,
        context: PipelineRunContext,
        table_name: str,
        rows: list[_StagedRow],
    ) -> None:
        insert_stage = text(
            f"""
            INSERT INTO staging.{table_name} (
                academic_year,
                destination_stage,
                school_urn,
                school_laestab,
                school_name,
                admission_policy,
                entry_gender,
                institution_group,
                institution_type,
                qualification_group,
                qualification_level,
                breakdown_topic,
                breakdown,
                data_type,
                cohort_count,
                overall_value,
                education_value,
                apprenticeship_value,
                employment_value,
                not_sustained_value,
                activity_unknown_value,
                fe_value,
                other_education_value,
                school_sixth_form_value,
                sixth_form_college_value,
                higher_education_value,
                source_file_url,
                source_updated_at_utc
            ) VALUES (
                :academic_year,
                :destination_stage,
                :school_urn,
                :school_laestab,
                :school_name,
                :admission_policy,
                :entry_gender,
                :institution_group,
                :institution_type,
                :qualification_group,
                :qualification_level,
                :breakdown_topic,
                :breakdown,
                :data_type,
                :cohort_count,
                :overall_value,
                :education_value,
                :apprenticeship_value,
                :employment_value,
                :not_sustained_value,
                :activity_unknown_value,
                :fe_value,
                :other_education_value,
                :school_sixth_form_value,
                :sixth_form_college_value,
                :higher_education_value,
                :source_file_url,
                :source_updated_at_utc
            )
            """
        )
        for chunk in chunked(rows, context.stage_chunk_size):
            connection.execute(insert_stage, [row.__dict__ for row in chunk])

    @staticmethod
    def _staging_table_name(
        context: PipelineRunContext,
        *,
        destination_stage: destinations_contract.DestinationStage,
    ) -> str:
        suffix = "ks4" if destination_stage == "ks4" else "16_to_18"
        return f"school_leaver_destinations__{suffix}__{context.run_id.hex}"


def _download_payload(
    *,
    source_reference: str,
    timeout_seconds: float,
) -> _DownloadedPayload:
    parsed = urllib.parse.urlparse(source_reference)
    if parsed.scheme in {"http", "https"}:
        request = urllib.request.Request(
            source_reference,
            headers={"User-Agent": "civitas-pipeline/0.1"},
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
            observed_content_type = response.headers.get("Content-Type")
            if observed_content_type is None or "csv" not in observed_content_type.casefold():
                raise ValueError(
                    "Leaver destinations source returned a non-CSV response "
                    f"for '{source_reference}'."
                )
            return _DownloadedPayload(
                source_reference=source_reference,
                body=body,
                observed_http_status=int(getattr(response, "status", 200)),
                observed_content_type=observed_content_type,
                observed_content_disposition=response.headers.get("Content-Disposition"),
                observed_middleware_rewrite=response.headers.get("x-middleware-rewrite"),
            )

    source_path = Path(source_reference)
    if not source_path.exists():
        raise FileNotFoundError(
            f"Configured leaver destinations source '{source_path}' was not found."
        )
    return _DownloadedPayload(
        source_reference=str(source_path),
        body=source_path.read_bytes(),
        observed_http_status=None,
        observed_content_type="text/csv",
        observed_content_disposition=f'attachment; filename="{source_path.name}"',
        observed_middleware_rewrite=None,
    )


def _inspect_downloaded_csv(
    *,
    body: bytes,
    destination_stage: destinations_contract.DestinationStage,
    observed_file_name: str | None,
) -> tuple[str, str, int, tuple[str, ...]]:
    if not body.strip():
        raise ValueError("Leaver destinations download returned an empty payload.")
    content = body.decode("utf-8-sig")
    reader = csv.DictReader(content.splitlines())
    if reader.fieldnames is None:
        raise ValueError("Leaver destinations CSV has no header row.")
    headers = tuple(reader.fieldnames)
    destinations_contract.validate_headers(
        destination_stage=destination_stage,
        headers=headers,
    )
    rows = list(reader)
    if not rows:
        raise ValueError("Leaver destinations CSV has no data rows.")
    destination_year = _derive_destination_year(rows)
    bronze_file_name = _resolve_bronze_file_name(
        observed_file_name=observed_file_name,
        destination_stage=destination_stage,
        destination_year=destination_year,
    )
    return destination_year, bronze_file_name, len(rows), headers


def _derive_destination_year(rows: list[dict[str, str]]) -> str:
    destination_years: set[str] = set()
    for row in rows:
        time_period = row.get("time_period")
        if time_period is None:
            continue
        academic_year = destinations_contract.parse_academic_year(time_period)
        start_year, end_year = academic_year.split("/")
        destination_years.add(f"{start_year}-{end_year}")
    if len(destination_years) != 1:
        raise ValueError(
            "Leaver destinations CSV must contain exactly one destination year per asset."
        )
    return next(iter(destination_years))


def _resolve_bronze_file_name(
    *,
    observed_file_name: str | None,
    destination_stage: destinations_contract.DestinationStage,
    destination_year: str,
) -> str:
    file_name = _parse_file_name_from_content_disposition(observed_file_name)
    if file_name is not None:
        return file_name

    normalized_year = destination_year.replace("-", "")
    prefix = "ees_ks4_inst_" if destination_stage == "ks4" else "ees_ks5_inst_"
    return f"{prefix}{normalized_year}.csv"


def _parse_file_name_from_content_disposition(content_disposition: str | None) -> str | None:
    if content_disposition is None:
        return None
    lowered_tokens = [token.strip() for token in content_disposition.split(";")]
    for token in lowered_tokens:
        if not token.casefold().startswith("filename="):
            continue
        candidate = token.split("=", 1)[1].strip().strip('"').strip("'")
        if candidate:
            return Path(candidate).name
    return None


def _asset_to_manifest_record(asset: _DownloadedAsset) -> dict[str, object]:
    return {
        "bronze_file_name": asset.bronze_file_name,
        "bronze_relative_path": asset.bronze_relative_path,
        "data_catalogue_url": asset.data_catalogue_url,
        "dataset_key": asset.destination_stage,
        "destination_stage": asset.destination_stage,
        "destination_year": asset.destination_year,
        "downloaded_at_utc": asset.downloaded_at_utc,
        "header_count": asset.header_count,
        "headers": list(asset.headers),
        "observed_content_disposition": asset.observed_content_disposition,
        "observed_content_type": asset.observed_content_type,
        "observed_http_status": asset.observed_http_status,
        "observed_middleware_rewrite": asset.observed_middleware_rewrite,
        "public_csv_route_url": asset.public_csv_route_url,
        "release_page_url": asset.release_page_url,
        "row_count": asset.row_count,
        "sha256": asset.sha256,
        "source_reference": asset.source_reference,
    }


def _write_asset_manifest(manifest_path: Path, asset: _DownloadedAsset) -> None:
    manifest_path.write_text(
        json.dumps(_asset_to_manifest_record(asset), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _load_manifest_assets(manifest_path: Path) -> tuple[_DownloadedAsset, ...]:
    if not manifest_path.exists():
        return ()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ()
    assets = payload.get("assets") if isinstance(payload, dict) else None
    if not isinstance(assets, list):
        return ()

    parsed_assets: list[_DownloadedAsset] = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        try:
            destination_stage = str(asset["destination_stage"]).strip()
            parsed_destination_stage: destinations_contract.DestinationStage
            if destination_stage == "ks4":
                parsed_destination_stage = "ks4"
            elif destination_stage == "16_to_18":
                parsed_destination_stage = "16_to_18"
            else:
                raise ValueError("invalid_destination_stage")
            parsed_assets.append(
                _DownloadedAsset(
                    destination_stage=parsed_destination_stage,
                    destination_year=str(asset["destination_year"]).strip(),
                    release_page_url=str(asset["release_page_url"]).strip(),
                    data_catalogue_url=str(asset["data_catalogue_url"]).strip(),
                    public_csv_route_url=str(asset["public_csv_route_url"]).strip(),
                    source_reference=str(asset["source_reference"]).strip(),
                    observed_http_status=_to_optional_int(asset.get("observed_http_status")),
                    observed_content_type=_to_optional_str(asset.get("observed_content_type")),
                    observed_content_disposition=_to_optional_str(
                        asset.get("observed_content_disposition")
                    ),
                    observed_middleware_rewrite=_to_optional_str(
                        asset.get("observed_middleware_rewrite")
                    ),
                    downloaded_at_utc=str(asset["downloaded_at_utc"]).strip(),
                    bronze_file_name=str(asset["bronze_file_name"]).strip(),
                    bronze_relative_path=str(asset["bronze_relative_path"]).strip(),
                    sha256=str(asset["sha256"]).strip(),
                    row_count=int(asset["row_count"]),
                    header_count=int(asset["header_count"]),
                    headers=tuple(str(header).strip() for header in asset["headers"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            return ()
    return tuple(parsed_assets)


def _sorted_staged_rows(
    rows_by_stage_and_key: Mapping[
        tuple[destinations_contract.DestinationStage, tuple[str, ...]],
        _StagedRow,
    ],
    *,
    destination_stage: destinations_contract.DestinationStage,
) -> list[_StagedRow]:
    matching_rows = [
        row
        for (row_stage, _), row in rows_by_stage_and_key.items()
        if row_stage == destination_stage
    ]
    return sorted(
        matching_rows,
        key=lambda row: (
            row.school_urn,
            row.school_laestab or "",
            row.academic_year,
            row.qualification_group,
            row.qualification_level,
            row.breakdown_topic,
            row.breakdown,
            row.data_type,
        ),
    )


def _aggregate_group_rows(
    *,
    urn: str,
    academic_year: str,
    destination_stage: str,
    qualification_group: str,
    qualification_level: str,
    breakdown_topic: str,
    breakdown: str,
    rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    values_by_data_type: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        data_type = str(row["data_type"])
        values_by_data_type[data_type] = row

    count_row = values_by_data_type.get("Number of students")
    percentage_row = values_by_data_type.get("Percentage")
    return {
        "urn": urn,
        "academic_year": academic_year,
        "destination_stage": destination_stage,
        "qualification_group": qualification_group,
        "qualification_level": qualification_level,
        "breakdown_topic": breakdown_topic,
        "breakdown": breakdown,
        "school_name": _single_value_or_first(rows, "school_name") or "Unknown",
        "school_laestab": _single_value_or_first(rows, "school_laestab"),
        "admission_policy": _single_value_or_first(rows, "admission_policy"),
        "entry_gender": _single_value_or_first(rows, "entry_gender"),
        "institution_group": _single_value_or_first(rows, "institution_group"),
        "institution_type": _single_value_or_first(rows, "institution_type"),
        "cohort_count": _to_optional_int(
            _single_value_or_first(rows, "cohort_count")
            if count_row is None
            else count_row.get("cohort_count")
        ),
        "overall_count": _row_float_to_int(count_row, "overall_value"),
        "overall_pct": _row_float(percentage_row, "overall_value"),
        "education_count": _row_float_to_int(count_row, "education_value"),
        "education_pct": _row_float(percentage_row, "education_value"),
        "apprenticeship_count": _row_float_to_int(count_row, "apprenticeship_value"),
        "apprenticeship_pct": _row_float(percentage_row, "apprenticeship_value"),
        "employment_count": _row_float_to_int(count_row, "employment_value"),
        "employment_pct": _row_float(percentage_row, "employment_value"),
        "not_sustained_count": _row_float_to_int(count_row, "not_sustained_value"),
        "not_sustained_pct": _row_float(percentage_row, "not_sustained_value"),
        "activity_unknown_count": _row_float_to_int(count_row, "activity_unknown_value"),
        "activity_unknown_pct": _row_float(percentage_row, "activity_unknown_value"),
        "fe_count": _row_float_to_int(count_row, "fe_value"),
        "fe_pct": _row_float(percentage_row, "fe_value"),
        "other_education_count": _row_float_to_int(count_row, "other_education_value"),
        "other_education_pct": _row_float(percentage_row, "other_education_value"),
        "school_sixth_form_count": _row_float_to_int(count_row, "school_sixth_form_value"),
        "school_sixth_form_pct": _row_float(percentage_row, "school_sixth_form_value"),
        "sixth_form_college_count": _row_float_to_int(count_row, "sixth_form_college_value"),
        "sixth_form_college_pct": _row_float(percentage_row, "sixth_form_college_value"),
        "higher_education_count": _row_float_to_int(count_row, "higher_education_value"),
        "higher_education_pct": _row_float(percentage_row, "higher_education_value"),
        "source_file_url": _single_value_or_first(rows, "source_file_url"),
        "source_updated_at_utc": _single_value_or_first(rows, "source_updated_at_utc"),
    }


def _row_float(row: Mapping[str, Any] | None, key: str) -> float | None:
    if row is None:
        return None
    return _to_optional_float(row.get(key))


def _row_float_to_int(row: Mapping[str, Any] | None, key: str) -> int | None:
    value = _row_float(row, key)
    if value is None:
        return None
    return int(round(value))


def _resolve_school_urn(
    *,
    staged_row: Mapping[str, Any],
    school_by_urn: Mapping[str, _SchoolJoinRow],
    schools_by_laestab: Mapping[str, list[_SchoolJoinRow]],
) -> tuple[str | None, str | None]:
    school_urn = _to_optional_str(staged_row.get("school_urn"))
    school_laestab = _to_optional_str(staged_row.get("school_laestab"))

    if school_urn is not None:
        matched_school = school_by_urn.get(school_urn)
        if matched_school is not None:
            if (
                school_laestab is not None
                and matched_school.school_laestab is not None
                and matched_school.school_laestab != school_laestab
            ):
                return None, "join_key_conflict"
            return matched_school.urn, None

    if school_laestab is None:
        if school_urn is None:
            return None, "missing_school_identifier"
        return None, "school_not_found"

    matches = schools_by_laestab.get(school_laestab, [])
    if len(matches) == 0:
        return None, "school_not_found"
    if len(matches) > 1:
        return None, "ambiguous_school_laestab"
    return matches[0].urn, None


def _single_value_or_none(rows: list[Mapping[str, Any]], key: str) -> Any:
    values = [row[key] for row in rows if row.get(key) is not None]
    distinct_values: list[Any] = []
    for value in values:
        if value not in distinct_values:
            distinct_values.append(value)
    if len(distinct_values) == 1:
        return distinct_values[0]
    return None


def _single_value_or_first(rows: list[Mapping[str, Any]], key: str) -> Any:
    single_value = _single_value_or_none(rows, key)
    if single_value is not None:
        return single_value
    for row in rows:
        value = row.get(key)
        if value is not None:
            return value
    return None


def _insert_rejections(
    connection,
    *,
    context: PipelineRunContext,
    stage: str,
    rejected_rows: list[tuple[str, dict[str, Any]]],
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
            :stage,
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
                    "stage": stage,
                    "reason_code": reason_code,
                    "raw_record": json.dumps(raw_row, ensure_ascii=True, default=str),
                }
                for reason_code, raw_row in rejected_chunk
            ],
        )


def _sha256_bytes(payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(payload)
    return digest.hexdigest()


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    return token or None


def _to_optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return int(stripped)
    return None


def _to_optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return float(stripped)
    return None
