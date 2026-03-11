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
from typing import cast

from sqlalchemy import text
from sqlalchemy.engine import Engine

from civitas.infrastructure.persistence.postgres_subject_performance_repository import (
    materialize_school_subject_summaries,
)

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import ks4_subject_performance as subject_contract

BRONZE_MANIFEST_FILE_NAME = "ks4_subject_performance.manifest.json"


@dataclass(frozen=True)
class _DownloadedAsset:
    academic_year: str
    source_reference: str
    release_page_url: str
    data_catalogue_url: str
    public_csv_route_url: str
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
    school_urn: str
    school_laestab: str | None
    school_name: str
    old_la_code: str | None
    new_la_code: str | None
    la_name: str | None
    source_version: str
    source_downloaded_at_utc: datetime
    establishment_type_group: str | None
    pupil_count: int | None
    qualification_type: str
    qualification_family: str
    qualification_detailed: str | None
    grade_structure: str
    subject: str
    discount_code: str | None
    subject_discount_group: str | None
    grade: str
    number_achieving: int | None
    source_file_url: str


class Ks4SubjectPerformancePipeline:
    source = PipelineSource.KS4_SUBJECT_PERFORMANCE

    def __init__(
        self,
        engine: Engine | None,
        *,
        source_csv: str | None = None,
        source_url: str,
        release_page_url: str,
        data_catalogue_url: str,
    ) -> None:
        self._engine = engine
        self._source_reference = source_csv or source_url
        self._source_url = source_url
        self._release_page_url = release_page_url
        self._data_catalogue_url = data_catalogue_url

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        payload = _download_payload(
            source_reference=self._source_reference,
            timeout_seconds=context.http_timeout_seconds,
        )
        academic_year, bronze_file_name, row_count, headers = _inspect_downloaded_csv(
            body=payload.body,
            observed_file_name=payload.observed_content_disposition,
        )
        asset_directory = context.bronze_source_path / academic_year.replace("/", "-")
        asset_directory.mkdir(parents=True, exist_ok=True)
        target_csv = asset_directory / bronze_file_name
        target_csv.write_bytes(payload.body)

        asset = _DownloadedAsset(
            academic_year=academic_year,
            source_reference=payload.source_reference,
            release_page_url=self._release_page_url,
            data_catalogue_url=self._data_catalogue_url,
            public_csv_route_url=self._source_url,
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

        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
        manifest_path.write_text(
            json.dumps(
                {
                    "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                    "normalization_contract_version": subject_contract.CONTRACT_VERSION,
                    "assets": [_asset_to_manifest_record(asset)],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return row_count

    def stage(self, context: PipelineRunContext) -> StageResult:
        if self._engine is None:
            raise ValueError("Pipeline engine is required for stage.")

        manifest_assets = _load_manifest_assets(
            context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
        )
        if not manifest_assets:
            raise FileNotFoundError(
                "KS4 subject performance manifest is missing; run download first."
            )

        rows_by_key: dict[tuple[str, ...], _StagedRow] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        for asset in manifest_assets:
            csv_path = context.bronze_source_path / asset.bronze_relative_path
            if not csv_path.exists():
                raise FileNotFoundError(
                    f"KS4 subject performance bronze file not found at '{csv_path}'."
                )
            with csv_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
                reader = csv.DictReader(file_handle)
                if reader.fieldnames is None:
                    raise ValueError(f"KS4 subject performance CSV '{csv_path}' has no header row.")
                subject_contract.validate_headers(tuple(reader.fieldnames))
                for raw_row in reader:
                    normalized_row, rejection = subject_contract.normalize_row(
                        raw_row,
                        source_file_url=asset.source_reference,
                    )
                    if normalized_row is None:
                        if rejection is not None:
                            rejected_rows.append((rejection, dict(raw_row)))
                        continue
                    staged_row = _StagedRow(
                        academic_year=normalized_row["academic_year"],
                        school_urn=normalized_row["school_urn"],
                        school_laestab=normalized_row["school_laestab"],
                        school_name=normalized_row["school_name"],
                        old_la_code=normalized_row["old_la_code"],
                        new_la_code=normalized_row["new_la_code"],
                        la_name=normalized_row["la_name"],
                        source_version=normalized_row["source_version"],
                        source_downloaded_at_utc=_parse_datetime(asset.downloaded_at_utc),
                        establishment_type_group=normalized_row["establishment_type_group"],
                        pupil_count=normalized_row["pupil_count"],
                        qualification_type=normalized_row["qualification_type"],
                        qualification_family=normalized_row["qualification_family"],
                        qualification_detailed=normalized_row["qualification_detailed"],
                        grade_structure=normalized_row["grade_structure"],
                        subject=normalized_row["subject"],
                        discount_code=normalized_row["discount_code"],
                        subject_discount_group=normalized_row["subject_discount_group"],
                        grade=normalized_row["grade"],
                        number_achieving=normalized_row["number_achieving"],
                        source_file_url=normalized_row["source_file_url"],
                    )
                    rows_by_key[_stage_key(staged_row)] = staged_row

        staged_rows = sorted(
            rows_by_key.values(),
            key=lambda row: (
                row.school_urn,
                row.academic_year,
                row.qualification_type,
                row.subject,
                row.grade,
                row.source_version,
                row.discount_code or "",
            ),
        )
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            self._recreate_stage_table(connection, table_name=self._staging_table_name(context))
            if staged_rows:
                self._insert_stage_rows(
                    connection,
                    context=context,
                    table_name=self._staging_table_name(context),
                    rows=staged_rows,
                )
            if rejected_rows:
                _insert_rejections(
                    connection,
                    context=context,
                    stage="stage",
                    rejected_rows=rejected_rows,
                )

        return StageResult(
            staged_rows=len(staged_rows),
            rejected_rows=len(rejected_rows),
            contract_version=subject_contract.CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        if self._engine is None:
            raise ValueError("Pipeline engine is required for promote.")

        with self._engine.begin() as connection:
            staged_rows = tuple(
                connection.execute(
                    text(f"SELECT * FROM staging.{self._staging_table_name(context)}")
                ).mappings()
            )
            known_urns = {
                str(row["urn"])
                for row in connection.execute(text("SELECT urn FROM schools")).mappings()
            }

            aggregated_rows: dict[tuple[str, ...], list[Mapping[str, object]]] = {}
            rejected_rows: list[tuple[str, dict[str, object]]] = []
            for staged_row in staged_rows:
                school_urn = str(staged_row["school_urn"])
                if school_urn not in known_urns:
                    rejected_rows.append(("school_not_found", dict(staged_row)))
                    continue
                mapped_row = cast(Mapping[str, object], staged_row)
                aggregated_rows.setdefault(_promote_key(mapped_row), []).append(mapped_row)

            final_rows = [
                _aggregate_promote_rows(rows) for _, rows in sorted(aggregated_rows.items())
            ]
            if rejected_rows:
                _insert_rejections(
                    connection,
                    context=context,
                    stage="promote",
                    rejected_rows=rejected_rows,
                )

            if final_rows:
                upsert = text(
                    """
                    INSERT INTO school_ks4_subject_results_yearly (
                        urn,
                        academic_year,
                        school_laestab,
                        school_name,
                        old_la_code,
                        new_la_code,
                        la_name,
                        source_version,
                        source_downloaded_at_utc,
                        establishment_type_group,
                        pupil_count,
                        qualification_type,
                        qualification_family,
                        qualification_detailed,
                        grade_structure,
                        subject,
                        discount_code,
                        subject_discount_group,
                        grade,
                        number_achieving,
                        source_file_url,
                        updated_at
                    ) VALUES (
                        :urn,
                        :academic_year,
                        :school_laestab,
                        :school_name,
                        :old_la_code,
                        :new_la_code,
                        :la_name,
                        :source_version,
                        :source_downloaded_at_utc,
                        :establishment_type_group,
                        :pupil_count,
                        :qualification_type,
                        :qualification_family,
                        :qualification_detailed,
                        :grade_structure,
                        :subject,
                        :discount_code,
                        :subject_discount_group,
                        :grade,
                        :number_achieving,
                        :source_file_url,
                        timezone('utc', now())
                    )
                    ON CONFLICT (
                        urn,
                        academic_year,
                        qualification_type,
                        subject,
                        grade,
                        source_version
                    ) DO UPDATE SET
                        school_laestab = excluded.school_laestab,
                        school_name = excluded.school_name,
                        old_la_code = excluded.old_la_code,
                        new_la_code = excluded.new_la_code,
                        la_name = excluded.la_name,
                        source_downloaded_at_utc = excluded.source_downloaded_at_utc,
                        establishment_type_group = excluded.establishment_type_group,
                        pupil_count = excluded.pupil_count,
                        qualification_family = excluded.qualification_family,
                        qualification_detailed = excluded.qualification_detailed,
                        grade_structure = excluded.grade_structure,
                        discount_code = excluded.discount_code,
                        subject_discount_group = excluded.subject_discount_group,
                        number_achieving = excluded.number_achieving,
                        source_file_url = excluded.source_file_url,
                        updated_at = timezone('utc', now())
                    """
                )
                for row_chunk in chunked(final_rows, context.promote_chunk_size):
                    connection.execute(upsert, row_chunk)

            materialize_school_subject_summaries(connection, key_stage="ks4")
            return len(final_rows)

    @staticmethod
    def _staging_table_name(context: PipelineRunContext) -> str:
        return f"school_ks4_subject_results__{context.run_id.hex}"

    @staticmethod
    def _recreate_stage_table(connection, *, table_name: str) -> None:
        connection.execute(text(f"DROP TABLE IF EXISTS staging.{table_name}"))
        connection.execute(
            text(
                f"""
                CREATE TABLE staging.{table_name} (
                    academic_year text NOT NULL,
                    school_urn text NOT NULL,
                    school_laestab text NULL,
                    school_name text NOT NULL,
                    old_la_code text NULL,
                    new_la_code text NULL,
                    la_name text NULL,
                    source_version text NOT NULL,
                    source_downloaded_at_utc timestamptz NOT NULL,
                    establishment_type_group text NULL,
                    pupil_count integer NULL,
                    qualification_type text NOT NULL,
                    qualification_family text NOT NULL,
                    qualification_detailed text NULL,
                    grade_structure text NOT NULL,
                    subject text NOT NULL,
                    discount_code text NULL,
                    subject_discount_group text NULL,
                    grade text NOT NULL,
                    number_achieving integer NULL,
                    source_file_url text NOT NULL
                )
                """
            )
        )

    @staticmethod
    def _insert_stage_rows(connection, *, context: PipelineRunContext, table_name: str, rows):
        insert_stage = text(
            f"""
            INSERT INTO staging.{table_name} (
                academic_year,
                school_urn,
                school_laestab,
                school_name,
                old_la_code,
                new_la_code,
                la_name,
                source_version,
                source_downloaded_at_utc,
                establishment_type_group,
                pupil_count,
                qualification_type,
                qualification_family,
                qualification_detailed,
                grade_structure,
                subject,
                discount_code,
                subject_discount_group,
                grade,
                number_achieving,
                source_file_url
            ) VALUES (
                :academic_year,
                :school_urn,
                :school_laestab,
                :school_name,
                :old_la_code,
                :new_la_code,
                :la_name,
                :source_version,
                :source_downloaded_at_utc,
                :establishment_type_group,
                :pupil_count,
                :qualification_type,
                :qualification_family,
                :qualification_detailed,
                :grade_structure,
                :subject,
                :discount_code,
                :subject_discount_group,
                :grade,
                :number_achieving,
                :source_file_url
            )
            """
        )
        for chunk in chunked(rows, context.stage_chunk_size):
            connection.execute(insert_stage, [row.__dict__ for row in chunk])


def _stage_key(row: _StagedRow) -> tuple[str, ...]:
    return (
        row.academic_year,
        row.school_urn,
        row.qualification_type,
        row.subject,
        row.grade,
        row.source_version,
        row.discount_code or "",
        row.subject_discount_group or "",
    )


def _promote_key(row: Mapping[str, object]) -> tuple[str, ...]:
    return (
        str(row["school_urn"]),
        str(row["academic_year"]),
        str(row["qualification_type"]),
        str(row["qualification_family"]),
        str(row["qualification_detailed"] or ""),
        str(row["grade_structure"]),
        str(row["subject"]),
        str(row["grade"]),
        str(row["source_version"]),
    )


def _aggregate_promote_rows(rows: list[Mapping[str, object]]) -> dict[str, object]:
    first_row = rows[0]
    number_achieving_total = sum(_to_optional_int(row.get("number_achieving")) or 0 for row in rows)
    return {
        "urn": str(first_row["school_urn"]),
        "academic_year": str(first_row["academic_year"]),
        "school_laestab": _single_value_or_first(rows, "school_laestab"),
        "school_name": _single_value_or_first(rows, "school_name") or "Unknown",
        "old_la_code": _single_value_or_first(rows, "old_la_code"),
        "new_la_code": _single_value_or_first(rows, "new_la_code"),
        "la_name": _single_value_or_first(rows, "la_name"),
        "source_version": str(first_row["source_version"]),
        "source_downloaded_at_utc": _single_value_or_first(rows, "source_downloaded_at_utc"),
        "establishment_type_group": _single_value_or_first(rows, "establishment_type_group"),
        "pupil_count": _to_optional_int(_single_value_or_first(rows, "pupil_count")),
        "qualification_type": str(first_row["qualification_type"]),
        "qualification_family": str(first_row["qualification_family"]),
        "qualification_detailed": _single_value_or_first(rows, "qualification_detailed"),
        "grade_structure": str(first_row["grade_structure"]),
        "subject": str(first_row["subject"]),
        "discount_code": _single_value_or_none(rows, "discount_code"),
        "subject_discount_group": _single_value_or_none(rows, "subject_discount_group"),
        "grade": str(first_row["grade"]),
        "number_achieving": number_achieving_total,
        "source_file_url": _single_value_or_first(rows, "source_file_url"),
    }


def _download_payload(*, source_reference: str, timeout_seconds: float) -> _DownloadedPayload:
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
                    "KS4 subject performance source returned a non-CSV response "
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
            f"Configured KS4 subject performance source '{source_path}' was not found."
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
    observed_file_name: str | None,
) -> tuple[str, str, int, tuple[str, ...]]:
    if not body.strip():
        raise ValueError("KS4 subject performance download returned an empty payload.")
    content = body.decode("utf-8-sig")
    reader = csv.DictReader(content.splitlines())
    if reader.fieldnames is None:
        raise ValueError("KS4 subject performance CSV has no header row.")
    headers = tuple(reader.fieldnames)
    subject_contract.validate_headers(headers)
    rows = list(reader)
    if not rows:
        raise ValueError("KS4 subject performance CSV has no data rows.")
    academic_year = _derive_academic_year(rows)
    bronze_file_name = _resolve_bronze_file_name(
        observed_file_name=observed_file_name,
        academic_year=academic_year,
    )
    return academic_year, bronze_file_name, len(rows), headers


def _derive_academic_year(rows: list[dict[str, str]]) -> str:
    academic_years = {
        subject_contract.parse_academic_year(row["time_period"])
        for row in rows
        if row.get("time_period")
    }
    if len(academic_years) != 1:
        raise ValueError("KS4 subject performance CSV must contain exactly one academic year.")
    return next(iter(academic_years))


def _resolve_bronze_file_name(*, observed_file_name: str | None, academic_year: str) -> str:
    file_name = _parse_file_name_from_content_disposition(observed_file_name)
    if file_name is not None:
        return file_name
    return f"ks4_subject_performance_{academic_year.replace('/', '')}.csv"


def _parse_file_name_from_content_disposition(content_disposition: str | None) -> str | None:
    if content_disposition is None:
        return None
    for token in (item.strip() for item in content_disposition.split(";")):
        if not token.casefold().startswith("filename="):
            continue
        candidate = token.split("=", 1)[1].strip().strip('"').strip("'")
        if candidate:
            return Path(candidate).name
    return None


def _asset_to_manifest_record(asset: _DownloadedAsset) -> dict[str, object]:
    return {
        "academic_year": asset.academic_year,
        "bronze_file_name": asset.bronze_file_name,
        "bronze_relative_path": asset.bronze_relative_path,
        "data_catalogue_url": asset.data_catalogue_url,
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
            parsed_assets.append(
                _DownloadedAsset(
                    academic_year=str(asset["academic_year"]).strip(),
                    source_reference=str(asset["source_reference"]).strip(),
                    release_page_url=str(asset["release_page_url"]).strip(),
                    data_catalogue_url=str(asset["data_catalogue_url"]).strip(),
                    public_csv_route_url=str(asset["public_csv_route_url"]).strip(),
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


def _insert_rejections(connection, *, context: PipelineRunContext, stage: str, rejected_rows):
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


def _single_value_or_none(rows: list[Mapping[str, object]], key: str) -> object:
    values = [row[key] for row in rows if row.get(key) is not None]
    distinct_values: list[object] = []
    for value in values:
        if value not in distinct_values:
            distinct_values.append(value)
    if len(distinct_values) == 1:
        return distinct_values[0]
    return None


def _single_value_or_first(rows: list[Mapping[str, object]], key: str) -> object:
    single_value = _single_value_or_none(rows, key)
    if single_value is not None:
        return single_value
    for row in rows:
        value = row.get(key)
        if value is not None:
            return value
    return None


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
