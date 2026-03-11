from __future__ import annotations

import csv
import hashlib
import json
import shutil
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
from .contracts import school_admissions as admissions_contract

BRONZE_FILE_NAME = "school_admissions.csv"
BRONZE_MANIFEST_FILE_NAME = "school_admissions.manifest.json"


@dataclass(frozen=True)
class _ManifestAsset:
    source_reference: str
    bronze_file_name: str
    downloaded_at: str
    sha256: str
    row_count: int
    release_version_id: str | None
    file_id: str | None


@dataclass(frozen=True)
class _StagedRow:
    academic_year: str
    entry_year: str | None
    school_urn: str | None
    school_laestab: str | None
    school_phase: str | None
    school_name: str
    places_offered_total: int | None
    preferred_offers_total: int | None
    first_preference_offers: int | None
    second_preference_offers: int | None
    third_preference_offers: int | None
    applications_any_preference: int | None
    applications_first_preference: int | None
    applications_second_preference: int | None
    applications_third_preference: int | None
    first_preference_application_to_offer_ratio: float | None
    first_preference_application_to_total_places_ratio: float | None
    cross_la_applications: int | None
    cross_la_offers: int | None
    admissions_policy: str | None
    establishment_type: str | None
    denomination: str | None
    fsm_eligible_pct: float | None
    urban_rural: str | None
    allthrough_school: bool | None
    source_file_url: str
    source_updated_at_utc: datetime


@dataclass(frozen=True)
class _SchoolJoinRow:
    urn: str
    school_laestab: str | None


class SchoolAdmissionsPipeline:
    source = PipelineSource.SCHOOL_ADMISSIONS

    def __init__(
        self,
        engine: Engine | None,
        *,
        source_csv: str | None = None,
        source_url: str | None = None,
    ) -> None:
        self._engine = engine
        self._source_csv = source_csv
        self._source_url = source_url

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)
        target_csv = context.bronze_source_path / BRONZE_FILE_NAME
        manifest_path = context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME

        cached_asset = _load_manifest_asset(manifest_path)
        if (
            target_csv.exists()
            and cached_asset is not None
            and cached_asset.sha256 == _sha256_file(target_csv)
        ):
            return cached_asset.row_count

        source_reference = self._source_csv or self._source_url
        if source_reference is None:
            raise RuntimeError(
                "Unable to download school admissions source automatically. Set "
                "CIVITAS_SCHOOL_ADMISSIONS_SOURCE_CSV or CIVITAS_SCHOOL_ADMISSIONS_SOURCE_URL."
            )

        _copy_from_source(source_reference, target_csv)
        row_count = _count_csv_rows(target_csv)
        release_version_id, file_id = _parse_release_identifiers(source_reference)
        asset = _ManifestAsset(
            source_reference=source_reference,
            bronze_file_name=BRONZE_FILE_NAME,
            downloaded_at=datetime.now(timezone.utc).isoformat(),
            sha256=_sha256_file(target_csv),
            row_count=row_count,
            release_version_id=release_version_id,
            file_id=file_id,
        )
        manifest_path.write_text(
            json.dumps(
                {
                    "downloaded_at": asset.downloaded_at,
                    "normalization_contract_version": admissions_contract.CONTRACT_VERSION,
                    "assets": [
                        {
                            "source_reference": asset.source_reference,
                            "bronze_file_name": asset.bronze_file_name,
                            "downloaded_at": asset.downloaded_at,
                            "sha256": asset.sha256,
                            "row_count": asset.row_count,
                            "release_version_id": asset.release_version_id,
                            "file_id": asset.file_id,
                        }
                    ],
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

        source_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if not source_csv.exists():
            raise FileNotFoundError(
                f"School admissions bronze file not found at '{source_csv}'. Run download first."
            )

        manifest_asset = _load_manifest_asset(
            context.bronze_source_path / BRONZE_MANIFEST_FILE_NAME
        )
        if manifest_asset is None:
            raise FileNotFoundError("School admissions manifest is missing; run download first.")

        rows_by_key: dict[tuple[str, str, str, str], _StagedRow] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        with source_csv.open("r", encoding="utf-8-sig", newline="") as file_handle:
            reader = csv.DictReader(file_handle)
            if reader.fieldnames is None:
                raise ValueError("School admissions CSV has no header row.")
            admissions_contract.validate_headers(tuple(reader.fieldnames))
            for raw_row in reader:
                normalized_row, rejection = admissions_contract.normalize_row(
                    raw_row,
                    source_file_url=manifest_asset.source_reference,
                )
                if normalized_row is None:
                    if rejection is not None:
                        rejected_rows.append((rejection, dict(raw_row)))
                    continue
                staged_row = _StagedRow(
                    academic_year=normalized_row["academic_year"],
                    entry_year=normalized_row["entry_year"],
                    school_urn=normalized_row["school_urn"],
                    school_laestab=normalized_row["school_laestab"],
                    school_phase=normalized_row["school_phase"],
                    school_name=normalized_row["school_name"],
                    places_offered_total=normalized_row["places_offered_total"],
                    preferred_offers_total=normalized_row["preferred_offers_total"],
                    first_preference_offers=normalized_row["first_preference_offers"],
                    second_preference_offers=normalized_row["second_preference_offers"],
                    third_preference_offers=normalized_row["third_preference_offers"],
                    applications_any_preference=normalized_row["applications_any_preference"],
                    applications_first_preference=normalized_row["applications_first_preference"],
                    applications_second_preference=normalized_row["applications_second_preference"],
                    applications_third_preference=normalized_row["applications_third_preference"],
                    first_preference_application_to_offer_ratio=normalized_row[
                        "first_preference_application_to_offer_ratio"
                    ],
                    first_preference_application_to_total_places_ratio=normalized_row[
                        "first_preference_application_to_total_places_ratio"
                    ],
                    cross_la_applications=normalized_row["cross_la_applications"],
                    cross_la_offers=normalized_row["cross_la_offers"],
                    admissions_policy=normalized_row["admissions_policy"],
                    establishment_type=normalized_row["establishment_type"],
                    denomination=normalized_row["denomination"],
                    fsm_eligible_pct=normalized_row["fsm_eligible_pct"],
                    urban_rural=normalized_row["urban_rural"],
                    allthrough_school=normalized_row["allthrough_school"],
                    source_file_url=normalized_row["source_file_url"],
                    source_updated_at_utc=_parse_datetime(manifest_asset.downloaded_at),
                )
                rows_by_key[
                    (
                        staged_row.school_urn or "",
                        staged_row.school_laestab or "",
                        staged_row.academic_year,
                        staged_row.entry_year or "",
                    )
                ] = staged_row

        staged_rows = sorted(
            rows_by_key.values(),
            key=lambda row: (
                row.school_urn or "",
                row.school_laestab or "",
                row.academic_year,
                row.entry_year or "",
            ),
        )
        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
            connection.execute(
                text(
                    f"""
                    CREATE TABLE staging.{staging_table_name} (
                        academic_year text NOT NULL,
                        entry_year text NULL,
                        school_urn text NULL,
                        school_laestab text NULL,
                        school_phase text NULL,
                        school_name text NOT NULL,
                        places_offered_total integer NULL,
                        preferred_offers_total integer NULL,
                        first_preference_offers integer NULL,
                        second_preference_offers integer NULL,
                        third_preference_offers integer NULL,
                        applications_any_preference integer NULL,
                        applications_first_preference integer NULL,
                        applications_second_preference integer NULL,
                        applications_third_preference integer NULL,
                        first_preference_application_to_offer_ratio double precision NULL,
                        first_preference_application_to_total_places_ratio double precision NULL,
                        cross_la_applications integer NULL,
                        cross_la_offers integer NULL,
                        admissions_policy text NULL,
                        establishment_type text NULL,
                        denomination text NULL,
                        fsm_eligible_pct double precision NULL,
                        urban_rural text NULL,
                        allthrough_school boolean NULL,
                        source_file_url text NOT NULL,
                        source_updated_at_utc timestamptz NOT NULL
                    )
                    """
                )
            )
            if staged_rows:
                staged_insert = text(
                    f"""
                    INSERT INTO staging.{staging_table_name} (
                        academic_year,
                        entry_year,
                        school_urn,
                        school_laestab,
                        school_phase,
                        school_name,
                        places_offered_total,
                        preferred_offers_total,
                        first_preference_offers,
                        second_preference_offers,
                        third_preference_offers,
                        applications_any_preference,
                        applications_first_preference,
                        applications_second_preference,
                        applications_third_preference,
                        first_preference_application_to_offer_ratio,
                        first_preference_application_to_total_places_ratio,
                        cross_la_applications,
                        cross_la_offers,
                        admissions_policy,
                        establishment_type,
                        denomination,
                        fsm_eligible_pct,
                        urban_rural,
                        allthrough_school,
                        source_file_url,
                        source_updated_at_utc
                    ) VALUES (
                        :academic_year,
                        :entry_year,
                        :school_urn,
                        :school_laestab,
                        :school_phase,
                        :school_name,
                        :places_offered_total,
                        :preferred_offers_total,
                        :first_preference_offers,
                        :second_preference_offers,
                        :third_preference_offers,
                        :applications_any_preference,
                        :applications_first_preference,
                        :applications_second_preference,
                        :applications_third_preference,
                        :first_preference_application_to_offer_ratio,
                        :first_preference_application_to_total_places_ratio,
                        :cross_la_applications,
                        :cross_la_offers,
                        :admissions_policy,
                        :establishment_type,
                        :denomination,
                        :fsm_eligible_pct,
                        :urban_rural,
                        :allthrough_school,
                        :source_file_url,
                        :source_updated_at_utc
                    )
                    """
                )
                for staged_chunk in chunked(staged_rows, context.stage_chunk_size):
                    connection.execute(staged_insert, [row.__dict__ for row in staged_chunk])

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
            contract_version=admissions_contract.CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        if self._engine is None:
            raise ValueError("Pipeline engine is required for promote.")

        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            staged_rows = tuple(
                connection.execute(text(f"SELECT * FROM staging.{staging_table_name}")).mappings()
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

            grouped_rows: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
            rejected_rows: list[tuple[str, dict[str, Any]]] = []
            for staged_row_record in staged_rows:
                staged_row = dict(staged_row_record)
                resolved_urn, rejection = _resolve_school_urn(
                    staged_row=staged_row,
                    school_by_urn=school_by_urn,
                    schools_by_laestab=schools_by_laestab,
                )
                if resolved_urn is None:
                    rejected_rows.append((rejection or "school_not_found", dict(staged_row)))
                    continue
                grouped_rows.setdefault(
                    (resolved_urn, str(staged_row["academic_year"])), []
                ).append(staged_row)

            aggregated_rows = [
                _aggregate_group_rows(urn=urn, academic_year=academic_year, rows=rows)
                for (urn, academic_year), rows in sorted(grouped_rows.items())
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
                    INSERT INTO school_admissions_yearly (
                        urn,
                        academic_year,
                        entry_year,
                        school_laestab,
                        school_phase,
                        school_name,
                        places_offered_total,
                        preferred_offers_total,
                        first_preference_offers,
                        second_preference_offers,
                        third_preference_offers,
                        applications_any_preference,
                        applications_first_preference,
                        applications_second_preference,
                        applications_third_preference,
                        first_preference_application_to_offer_ratio,
                        first_preference_application_to_total_places_ratio,
                        cross_la_applications,
                        cross_la_offers,
                        admissions_policy,
                        establishment_type,
                        denomination,
                        fsm_eligible_pct,
                        urban_rural,
                        allthrough_school,
                        oversubscription_ratio,
                        first_preference_offer_rate,
                        any_preference_offer_rate,
                        source_file_url,
                        source_updated_at_utc,
                        updated_at
                    ) VALUES (
                        :urn,
                        :academic_year,
                        :entry_year,
                        :school_laestab,
                        :school_phase,
                        :school_name,
                        :places_offered_total,
                        :preferred_offers_total,
                        :first_preference_offers,
                        :second_preference_offers,
                        :third_preference_offers,
                        :applications_any_preference,
                        :applications_first_preference,
                        :applications_second_preference,
                        :applications_third_preference,
                        :first_preference_application_to_offer_ratio,
                        :first_preference_application_to_total_places_ratio,
                        :cross_la_applications,
                        :cross_la_offers,
                        :admissions_policy,
                        :establishment_type,
                        :denomination,
                        :fsm_eligible_pct,
                        :urban_rural,
                        :allthrough_school,
                        :oversubscription_ratio,
                        :first_preference_offer_rate,
                        :any_preference_offer_rate,
                        :source_file_url,
                        :source_updated_at_utc,
                        timezone('utc', now())
                    )
                    ON CONFLICT (urn, academic_year) DO UPDATE SET
                        entry_year = EXCLUDED.entry_year,
                        school_laestab = EXCLUDED.school_laestab,
                        school_phase = EXCLUDED.school_phase,
                        school_name = EXCLUDED.school_name,
                        places_offered_total = EXCLUDED.places_offered_total,
                        preferred_offers_total = EXCLUDED.preferred_offers_total,
                        first_preference_offers = EXCLUDED.first_preference_offers,
                        second_preference_offers = EXCLUDED.second_preference_offers,
                        third_preference_offers = EXCLUDED.third_preference_offers,
                        applications_any_preference = EXCLUDED.applications_any_preference,
                        applications_first_preference = EXCLUDED.applications_first_preference,
                        applications_second_preference = EXCLUDED.applications_second_preference,
                        applications_third_preference = EXCLUDED.applications_third_preference,
                        first_preference_application_to_offer_ratio =
                            EXCLUDED.first_preference_application_to_offer_ratio,
                        first_preference_application_to_total_places_ratio =
                            EXCLUDED.first_preference_application_to_total_places_ratio,
                        cross_la_applications = EXCLUDED.cross_la_applications,
                        cross_la_offers = EXCLUDED.cross_la_offers,
                        admissions_policy = EXCLUDED.admissions_policy,
                        establishment_type = EXCLUDED.establishment_type,
                        denomination = EXCLUDED.denomination,
                        fsm_eligible_pct = EXCLUDED.fsm_eligible_pct,
                        urban_rural = EXCLUDED.urban_rural,
                        allthrough_school = EXCLUDED.allthrough_school,
                        oversubscription_ratio = EXCLUDED.oversubscription_ratio,
                        first_preference_offer_rate = EXCLUDED.first_preference_offer_rate,
                        any_preference_offer_rate = EXCLUDED.any_preference_offer_rate,
                        source_file_url = EXCLUDED.source_file_url,
                        source_updated_at_utc = EXCLUDED.source_updated_at_utc,
                        updated_at = timezone('utc', now())
                    """
                )
                for chunk in chunked(aggregated_rows, context.promote_chunk_size):
                    result = connection.execute(upsert, chunk)
                    promoted_rows += int(result.rowcount or 0)

            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
        return promoted_rows

    @staticmethod
    def _staging_table_name(context: PipelineRunContext) -> str:
        return f"school_admissions__{context.run_id.hex}"


def _aggregate_group_rows(
    *,
    urn: str,
    academic_year: str,
    rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "urn": urn,
        "academic_year": academic_year,
        "entry_year": _single_value_or_none(rows, "entry_year"),
        "school_laestab": _single_value_or_none(rows, "school_laestab"),
        "school_phase": _single_value_or_none(rows, "school_phase"),
        "school_name": _single_value_or_first(rows, "school_name") or "Unknown",
        "places_offered_total": _sum_optional_int(rows, "places_offered_total"),
        "preferred_offers_total": _sum_optional_int(rows, "preferred_offers_total"),
        "first_preference_offers": _sum_optional_int(rows, "first_preference_offers"),
        "second_preference_offers": _sum_optional_int(rows, "second_preference_offers"),
        "third_preference_offers": _sum_optional_int(rows, "third_preference_offers"),
        "applications_any_preference": _sum_optional_int(rows, "applications_any_preference"),
        "applications_first_preference": _sum_optional_int(rows, "applications_first_preference"),
        "applications_second_preference": _sum_optional_int(rows, "applications_second_preference"),
        "applications_third_preference": _sum_optional_int(rows, "applications_third_preference"),
        "first_preference_application_to_offer_ratio": (
            _single_row_ratio_or_none(rows, "first_preference_application_to_offer_ratio")
        ),
        "first_preference_application_to_total_places_ratio": (
            _single_row_ratio_or_none(rows, "first_preference_application_to_total_places_ratio")
        ),
        "cross_la_applications": _sum_optional_int(rows, "cross_la_applications"),
        "cross_la_offers": _sum_optional_int(rows, "cross_la_offers"),
        "admissions_policy": _single_value_or_first(rows, "admissions_policy"),
        "establishment_type": _single_value_or_first(rows, "establishment_type"),
        "denomination": _single_value_or_first(rows, "denomination"),
        "fsm_eligible_pct": _single_value_or_first(rows, "fsm_eligible_pct"),
        "urban_rural": _single_value_or_first(rows, "urban_rural"),
        "allthrough_school": _aggregate_allthrough(rows),
        "oversubscription_ratio": _safe_divide(
            _sum_optional_int(rows, "applications_any_preference"),
            _sum_optional_int(rows, "places_offered_total"),
        ),
        "first_preference_offer_rate": _safe_divide(
            _sum_optional_int(rows, "first_preference_offers"),
            _sum_optional_int(rows, "applications_first_preference"),
        ),
        "any_preference_offer_rate": _safe_divide(
            _sum_optional_int(rows, "preferred_offers_total"),
            _sum_optional_int(rows, "applications_any_preference"),
        ),
        "source_file_url": _single_value_or_first(rows, "source_file_url"),
        "source_updated_at_utc": _single_value_or_first(rows, "source_updated_at_utc"),
    }


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


def _single_row_ratio_or_none(rows: list[Mapping[str, Any]], key: str) -> float | None:
    if len(rows) != 1:
        return None
    return _to_optional_float(rows[0].get(key))


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


def _aggregate_allthrough(rows: list[Mapping[str, Any]]) -> bool | None:
    values = [_to_optional_bool(row.get("allthrough_school")) for row in rows]
    if any(value is True for value in values):
        return True
    if any(value is False for value in values):
        return False
    return None


def _sum_optional_int(rows: list[Mapping[str, Any]], key: str) -> int | None:
    values = [_to_optional_int(row.get(key)) for row in rows]
    present_values = [value for value in values if value is not None]
    if not present_values:
        return None
    return sum(present_values)


def _safe_divide(numerator: int | None, denominator: int | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return float(numerator) / float(denominator)


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


def _parse_release_identifiers(source_reference: str) -> tuple[str | None, str | None]:
    parsed = urllib.parse.urlparse(source_reference)
    if parsed.scheme not in {"http", "https"}:
        return None, None
    tokens = [token for token in parsed.path.split("/") if token]
    try:
        release_index = tokens.index("releases")
        file_index = tokens.index("files")
    except ValueError:
        return None, None
    if release_index + 1 >= len(tokens) or file_index + 1 >= len(tokens):
        return None, None
    return tokens[release_index + 1], tokens[file_index + 1]


def _load_manifest_asset(manifest_path: Path) -> _ManifestAsset | None:
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    assets = payload.get("assets") if isinstance(payload, dict) else None
    if not isinstance(assets, list) or len(assets) == 0 or not isinstance(assets[0], dict):
        return None
    asset = assets[0]
    try:
        return _ManifestAsset(
            source_reference=str(asset["source_reference"]).strip(),
            bronze_file_name=str(asset["bronze_file_name"]).strip(),
            downloaded_at=str(asset["downloaded_at"]).strip(),
            sha256=str(asset["sha256"]).strip(),
            row_count=int(asset["row_count"]),
            release_version_id=_to_optional_str(asset.get("release_version_id")),
            file_id=_to_optional_str(asset.get("file_id")),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file_handle:
        row_count_with_header = sum(1 for _ in csv.reader(file_handle))
    return max(0, row_count_with_header - 1)


def _copy_from_source(source: str, target: Path) -> None:
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        request = urllib.request.Request(source, headers={"User-Agent": "civitas-pipeline/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response:
            target.write_bytes(response.read())
        return

    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"Configured source CSV path '{source_path}' was not found.")
    shutil.copy2(source_path, target)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
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


def _to_optional_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip().casefold()
        if not stripped:
            return None
        if stripped == "true":
            return True
        if stripped == "false":
            return False
    return None
