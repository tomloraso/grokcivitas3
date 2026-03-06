from __future__ import annotations

import csv
import hashlib
import json
import logging
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import gias as gias_contract

REQUIRED_GIAS_HEADERS = gias_contract.REQUIRED_HEADERS

BRONZE_FILE_NAME = "edubasealldata.csv"
CSV_NAME_SUBSTRING = "edubasealldata"

# GIAS bulk extracts from get-information-schools.service.gov.uk are
# encoded as Windows-1252 (cp1252).  School names frequently contain
# Windows-style right single quotes (\x92) and other characters outside
# the ASCII/UTF-8 range.  cp1252 is a strict superset of ASCII so test
# fixtures authored in plain ASCII are decoded correctly.
GIAS_CSV_ENCODING = "cp1252"
GIAS_NORMALIZATION_CONTRACT_VERSION = gias_contract.CONTRACT_VERSION
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GiasStagedRow:
    urn: str
    name: str
    phase: str | None
    school_type: str | None
    status: str | None
    postcode: str | None
    easting: float
    northing: float
    open_date: date | None
    close_date: date | None
    pupil_count: int | None
    capacity: int | None
    website: str | None
    telephone: str | None
    head_title: str | None
    head_first_name: str | None
    head_last_name: str | None
    head_job_title: str | None
    address_street: str | None
    address_locality: str | None
    address_line3: str | None
    address_town: str | None
    address_county: str | None
    statutory_low_age: int | None
    statutory_high_age: int | None
    gender: str | None
    religious_character: str | None
    diocese: str | None
    admissions_policy: str | None
    sixth_form: str | None
    nursery_provision: str | None
    boarders: str | None
    fsm_pct_gias: float | None
    trust_name: str | None
    trust_flag: str | None
    federation_name: str | None
    federation_flag: str | None
    la_name: str | None
    la_code: str | None
    urban_rural: str | None
    number_of_boys: int | None
    number_of_girls: int | None
    lsoa_code: str | None
    lsoa_name: str | None
    last_changed_date: date | None


def normalize_gias_postcode(raw_postcode: str | None) -> str | None:
    return gias_contract.normalize_postcode(raw_postcode)


def validate_gias_headers(headers: Sequence[str]) -> None:
    gias_contract.validate_headers(headers)


def normalize_gias_row(
    raw_row: Mapping[str, str],
) -> tuple[GiasStagedRow | None, str | None, tuple[gias_contract.NormalizationWarning, ...]]:
    normalized_row, rejection, warnings = gias_contract.normalize_row(raw_row)
    if normalized_row is None:
        return None, rejection, warnings
    return (
        GiasStagedRow(
            urn=normalized_row["urn"],
            name=normalized_row["name"],
            phase=normalized_row["phase"],
            school_type=normalized_row["school_type"],
            status=normalized_row["status"],
            postcode=normalized_row["postcode"],
            easting=normalized_row["easting"],
            northing=normalized_row["northing"],
            open_date=normalized_row["open_date"],
            close_date=normalized_row["close_date"],
            pupil_count=normalized_row["pupil_count"],
            capacity=normalized_row["capacity"],
            website=normalized_row["website"],
            telephone=normalized_row["telephone"],
            head_title=normalized_row["head_title"],
            head_first_name=normalized_row["head_first_name"],
            head_last_name=normalized_row["head_last_name"],
            head_job_title=normalized_row["head_job_title"],
            address_street=normalized_row["address_street"],
            address_locality=normalized_row["address_locality"],
            address_line3=normalized_row["address_line3"],
            address_town=normalized_row["address_town"],
            address_county=normalized_row["address_county"],
            statutory_low_age=normalized_row["statutory_low_age"],
            statutory_high_age=normalized_row["statutory_high_age"],
            gender=normalized_row["gender"],
            religious_character=normalized_row["religious_character"],
            diocese=normalized_row["diocese"],
            admissions_policy=normalized_row["admissions_policy"],
            sixth_form=normalized_row["sixth_form"],
            nursery_provision=normalized_row["nursery_provision"],
            boarders=normalized_row["boarders"],
            fsm_pct_gias=normalized_row["fsm_pct_gias"],
            trust_name=normalized_row["trust_name"],
            trust_flag=normalized_row["trust_flag"],
            federation_name=normalized_row["federation_name"],
            federation_flag=normalized_row["federation_flag"],
            la_name=normalized_row["la_name"],
            la_code=normalized_row["la_code"],
            urban_rural=normalized_row["urban_rural"],
            number_of_boys=normalized_row["number_of_boys"],
            number_of_girls=normalized_row["number_of_girls"],
            lsoa_code=normalized_row["lsoa_code"],
            lsoa_name=normalized_row["lsoa_name"],
            last_changed_date=normalized_row["last_changed_date"],
        ),
        None,
        warnings,
    )


class GiasPipeline:
    source = PipelineSource.GIAS

    def __init__(
        self,
        engine: Engine,
        source_csv: str | None = None,
        source_zip: str | None = None,
    ) -> None:
        self._engine = engine
        self._source_csv = source_csv
        self._source_zip = source_zip

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)

        target_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if target_csv.exists():
            return _count_csv_rows(target_csv)

        if self._source_csv:
            _copy_from_source(self._source_csv, target_csv)
            return self._finalize_download_metadata(target_csv, self._source_csv)

        if self._source_zip:
            _extract_csv_from_zip_source(self._source_zip, target_csv)
            return self._finalize_download_metadata(target_csv, self._source_zip)

        raise RuntimeError(
            "Unable to download GIAS source automatically. Set CIVITAS_GIAS_SOURCE_CSV "
            "or CIVITAS_GIAS_SOURCE_ZIP to a local path or URL."
        )

    def stage(self, context: PipelineRunContext) -> StageResult:
        source_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if not source_csv.exists():
            raise FileNotFoundError(
                f"GIAS bronze file not found at '{source_csv}'. Run download stage first."
            )

        staged_rows: list[GiasStagedRow] = []
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        normalization_warnings: list[tuple[str, gias_contract.NormalizationWarning]] = []
        with source_csv.open("r", encoding=GIAS_CSV_ENCODING, newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise ValueError("GIAS CSV has no header row.")

            validate_gias_headers(reader.fieldnames)

            for raw_row in reader:
                normalized, rejection, warnings = normalize_gias_row(raw_row)
                if normalized is not None:
                    staged_rows.append(normalized)
                    for warning in warnings:
                        normalization_warnings.append((normalized.urn, warning))
                    continue
                if rejection is not None:
                    rejected_rows.append((rejection, dict(raw_row)))

        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
            connection.execute(
                text(
                    f"""
                    CREATE TABLE staging.{staging_table_name} (
                        urn text PRIMARY KEY,
                        name text NOT NULL,
                        phase text NULL,
                        type text NULL,
                        status text NULL,
                        postcode text NULL,
                        easting double precision NOT NULL,
                        northing double precision NOT NULL,
                        open_date date NULL,
                        close_date date NULL,
                        pupil_count integer NULL,
                        capacity integer NULL,
                        website text NULL,
                        telephone text NULL,
                        head_title text NULL,
                        head_first_name text NULL,
                        head_last_name text NULL,
                        head_job_title text NULL,
                        address_street text NULL,
                        address_locality text NULL,
                        address_line3 text NULL,
                        address_town text NULL,
                        address_county text NULL,
                        statutory_low_age integer NULL,
                        statutory_high_age integer NULL,
                        gender text NULL,
                        religious_character text NULL,
                        diocese text NULL,
                        admissions_policy text NULL,
                        sixth_form text NULL,
                        nursery_provision text NULL,
                        boarders text NULL,
                        fsm_pct_gias double precision NULL,
                        trust_name text NULL,
                        trust_flag text NULL,
                        federation_name text NULL,
                        federation_flag text NULL,
                        la_name text NULL,
                        la_code text NULL,
                        urban_rural text NULL,
                        number_of_boys integer NULL,
                        number_of_girls integer NULL,
                        lsoa_code text NULL,
                        lsoa_name text NULL,
                        last_changed_date date NULL
                    )
                    """
                )
            )

            if staged_rows:
                staged_insert = text(
                    f"""
                    INSERT INTO staging.{staging_table_name} (
                        urn,
                        name,
                        phase,
                        type,
                        status,
                        postcode,
                        easting,
                        northing,
                        open_date,
                        close_date,
                        pupil_count,
                        capacity,
                        website,
                        telephone,
                        head_title,
                        head_first_name,
                        head_last_name,
                        head_job_title,
                        address_street,
                        address_locality,
                        address_line3,
                        address_town,
                        address_county,
                        statutory_low_age,
                        statutory_high_age,
                        gender,
                        religious_character,
                        diocese,
                        admissions_policy,
                        sixth_form,
                        nursery_provision,
                        boarders,
                        fsm_pct_gias,
                        trust_name,
                        trust_flag,
                        federation_name,
                        federation_flag,
                        la_name,
                        la_code,
                        urban_rural,
                        number_of_boys,
                        number_of_girls,
                        lsoa_code,
                        lsoa_name,
                        last_changed_date
                    ) VALUES (
                        :urn,
                        :name,
                        :phase,
                        :type,
                        :status,
                        :postcode,
                        :easting,
                        :northing,
                        :open_date,
                        :close_date,
                        :pupil_count,
                        :capacity,
                        :website,
                        :telephone,
                        :head_title,
                        :head_first_name,
                        :head_last_name,
                        :head_job_title,
                        :address_street,
                        :address_locality,
                        :address_line3,
                        :address_town,
                        :address_county,
                        :statutory_low_age,
                        :statutory_high_age,
                        :gender,
                        :religious_character,
                        :diocese,
                        :admissions_policy,
                        :sixth_form,
                        :nursery_provision,
                        :boarders,
                        :fsm_pct_gias,
                        :trust_name,
                        :trust_flag,
                        :federation_name,
                        :federation_flag,
                        :la_name,
                        :la_code,
                        :urban_rural,
                        :number_of_boys,
                        :number_of_girls,
                        :lsoa_code,
                        :lsoa_name,
                        :last_changed_date
                    )
                    """
                )
                for rows_chunk in chunked(staged_rows, context.stage_chunk_size):
                    connection.execute(
                        staged_insert,
                        [
                            {
                                "urn": row.urn,
                                "name": row.name,
                                "phase": row.phase,
                                "type": row.school_type,
                                "status": row.status,
                                "postcode": row.postcode,
                                "easting": row.easting,
                                "northing": row.northing,
                                "open_date": row.open_date,
                                "close_date": row.close_date,
                                "pupil_count": row.pupil_count,
                                "capacity": row.capacity,
                                "website": row.website,
                                "telephone": row.telephone,
                                "head_title": row.head_title,
                                "head_first_name": row.head_first_name,
                                "head_last_name": row.head_last_name,
                                "head_job_title": row.head_job_title,
                                "address_street": row.address_street,
                                "address_locality": row.address_locality,
                                "address_line3": row.address_line3,
                                "address_town": row.address_town,
                                "address_county": row.address_county,
                                "statutory_low_age": row.statutory_low_age,
                                "statutory_high_age": row.statutory_high_age,
                                "gender": row.gender,
                                "religious_character": row.religious_character,
                                "diocese": row.diocese,
                                "admissions_policy": row.admissions_policy,
                                "sixth_form": row.sixth_form,
                                "nursery_provision": row.nursery_provision,
                                "boarders": row.boarders,
                                "fsm_pct_gias": row.fsm_pct_gias,
                                "trust_name": row.trust_name,
                                "trust_flag": row.trust_flag,
                                "federation_name": row.federation_name,
                                "federation_flag": row.federation_flag,
                                "la_name": row.la_name,
                                "la_code": row.la_code,
                                "urban_rural": row.urban_rural,
                                "number_of_boys": row.number_of_boys,
                                "number_of_girls": row.number_of_girls,
                                "lsoa_code": row.lsoa_code,
                                "lsoa_name": row.lsoa_name,
                                "last_changed_date": row.last_changed_date,
                            }
                            for row in rows_chunk
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

            if normalization_warnings:
                for urn, warning in normalization_warnings:
                    logger.info(
                        "pipeline_normalization_warning",
                        extra={
                            "run_id": str(context.run_id),
                            "source": context.source.value,
                            "urn": urn,
                            "field_name": warning["field_name"],
                            "reason_code": warning["reason_code"],
                            "raw_value": warning["raw_value"],
                        },
                    )

                if _table_exists(connection, "pipeline_normalization_warnings"):
                    warning_counts = Counter(
                        (warning["field_name"], warning["reason_code"])
                        for _, warning in normalization_warnings
                    )
                    warning_insert = text(
                        """
                        INSERT INTO pipeline_normalization_warnings (
                            run_id,
                            source,
                            field_name,
                            reason_code,
                            warning_count
                        ) VALUES (
                            :run_id,
                            :source,
                            :field_name,
                            :reason_code,
                            :warning_count
                        )
                        """
                    )
                    connection.execute(
                        warning_insert,
                        [
                            {
                                "run_id": str(context.run_id),
                                "source": context.source.value,
                                "field_name": field_name,
                                "reason_code": reason_code,
                                "warning_count": warning_count,
                            }
                            for (field_name, reason_code), warning_count in sorted(
                                warning_counts.items()
                            )
                        ],
                    )

        return StageResult(
            staged_rows=len(staged_rows),
            rejected_rows=len(rejected_rows),
            contract_version=GIAS_NORMALIZATION_CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            promoted_rows = int(
                connection.execute(
                    text(
                        f"""
                        WITH upserted AS (
                            INSERT INTO schools (
                                urn,
                                name,
                                phase,
                                type,
                                status,
                                postcode,
                                easting,
                                northing,
                                location,
                                capacity,
                                pupil_count,
                                open_date,
                                close_date,
                                website,
                                telephone,
                                head_title,
                                head_first_name,
                                head_last_name,
                                head_job_title,
                                address_street,
                                address_locality,
                                address_line3,
                                address_town,
                                address_county,
                                statutory_low_age,
                                statutory_high_age,
                                gender,
                                religious_character,
                                diocese,
                                admissions_policy,
                                sixth_form,
                                nursery_provision,
                                boarders,
                                fsm_pct_gias,
                                trust_name,
                                trust_flag,
                                federation_name,
                                federation_flag,
                                la_name,
                                la_code,
                                urban_rural,
                                number_of_boys,
                                number_of_girls,
                                lsoa_code,
                                lsoa_name,
                                last_changed_date,
                                updated_at
                            )
                            SELECT
                                urn,
                                name,
                                phase,
                                type,
                                status,
                                postcode,
                                easting,
                                northing,
                                ST_Transform(
                                    ST_SetSRID(ST_MakePoint(easting, northing), 27700),
                                    4326
                                )::geography(Point, 4326),
                                capacity,
                                pupil_count,
                                open_date,
                                close_date,
                                website,
                                telephone,
                                head_title,
                                head_first_name,
                                head_last_name,
                                head_job_title,
                                address_street,
                                address_locality,
                                address_line3,
                                address_town,
                                address_county,
                                statutory_low_age,
                                statutory_high_age,
                                gender,
                                religious_character,
                                diocese,
                                admissions_policy,
                                sixth_form,
                                nursery_provision,
                                boarders,
                                fsm_pct_gias,
                                trust_name,
                                trust_flag,
                                federation_name,
                                federation_flag,
                                la_name,
                                la_code,
                                urban_rural,
                                number_of_boys,
                                number_of_girls,
                                lsoa_code,
                                lsoa_name,
                                last_changed_date,
                                timezone('utc', now())
                            FROM staging.{staging_table_name}
                            ON CONFLICT (urn) DO UPDATE SET
                                name = EXCLUDED.name,
                                phase = EXCLUDED.phase,
                                type = EXCLUDED.type,
                                status = EXCLUDED.status,
                                postcode = EXCLUDED.postcode,
                                easting = EXCLUDED.easting,
                                northing = EXCLUDED.northing,
                                location = EXCLUDED.location,
                                capacity = EXCLUDED.capacity,
                                pupil_count = EXCLUDED.pupil_count,
                                open_date = EXCLUDED.open_date,
                                close_date = EXCLUDED.close_date,
                                website = EXCLUDED.website,
                                telephone = EXCLUDED.telephone,
                                head_title = EXCLUDED.head_title,
                                head_first_name = EXCLUDED.head_first_name,
                                head_last_name = EXCLUDED.head_last_name,
                                head_job_title = EXCLUDED.head_job_title,
                                address_street = EXCLUDED.address_street,
                                address_locality = EXCLUDED.address_locality,
                                address_line3 = EXCLUDED.address_line3,
                                address_town = EXCLUDED.address_town,
                                address_county = EXCLUDED.address_county,
                                statutory_low_age = EXCLUDED.statutory_low_age,
                                statutory_high_age = EXCLUDED.statutory_high_age,
                                gender = EXCLUDED.gender,
                                religious_character = EXCLUDED.religious_character,
                                diocese = EXCLUDED.diocese,
                                admissions_policy = EXCLUDED.admissions_policy,
                                sixth_form = EXCLUDED.sixth_form,
                                nursery_provision = EXCLUDED.nursery_provision,
                                boarders = EXCLUDED.boarders,
                                fsm_pct_gias = EXCLUDED.fsm_pct_gias,
                                trust_name = EXCLUDED.trust_name,
                                trust_flag = EXCLUDED.trust_flag,
                                federation_name = EXCLUDED.federation_name,
                                federation_flag = EXCLUDED.federation_flag,
                                la_name = EXCLUDED.la_name,
                                la_code = EXCLUDED.la_code,
                                urban_rural = EXCLUDED.urban_rural,
                                number_of_boys = EXCLUDED.number_of_boys,
                                number_of_girls = EXCLUDED.number_of_girls,
                                lsoa_code = EXCLUDED.lsoa_code,
                                lsoa_name = EXCLUDED.lsoa_name,
                                last_changed_date = EXCLUDED.last_changed_date,
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

    @staticmethod
    def _staging_table_name(context: PipelineRunContext) -> str:
        return f"gias_schools__{context.run_id.hex}"

    def _finalize_download_metadata(self, target_csv: Path, source_reference: str) -> int:
        row_count = _count_csv_rows(target_csv)
        metadata_path = target_csv.with_suffix(".metadata.json")
        metadata = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "source_reference": source_reference,
            "normalization_contract_version": GIAS_NORMALIZATION_CONTRACT_VERSION,
            "sha256": _sha256_file(target_csv),
            "rows": row_count,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        return row_count


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding=GIAS_CSV_ENCODING, newline="") as csv_file:
        row_count_with_header = sum(1 for _ in csv.reader(csv_file))
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


def _extract_csv_from_zip_source(source: str, target_csv: Path) -> None:
    parsed = urllib.parse.urlparse(source)
    zip_path: Path | None = None

    if parsed.scheme in {"http", "https"}:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
            temp_zip_path = Path(temp_zip.name)

        try:
            request = urllib.request.Request(source, headers={"User-Agent": "civitas-pipeline/0.1"})
            with urllib.request.urlopen(request, timeout=60) as response:
                temp_zip_path.write_bytes(response.read())
            zip_path = temp_zip_path
            _extract_matching_csv(zip_path, target_csv)
        finally:
            if temp_zip_path.exists():
                temp_zip_path.unlink()
        return

    zip_path = Path(source)
    if not zip_path.exists():
        raise FileNotFoundError(f"Configured source ZIP path '{zip_path}' was not found.")
    _extract_matching_csv(zip_path, target_csv)


def _extract_matching_csv(zip_path: Path, target_csv: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as archive:
        csv_names = [
            item
            for item in archive.namelist()
            if item.lower().endswith(".csv") and CSV_NAME_SUBSTRING in item.lower()
        ]
        if not csv_names:
            raise ValueError(
                f"No CSV matching '{CSV_NAME_SUBSTRING}' was found in archive '{zip_path}'."
            )

        selected_csv = csv_names[0]
        with archive.open(selected_csv, "r") as source_file:
            target_csv.write_bytes(source_file.read())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _table_exists(connection: Connection, table_name: str) -> bool:
    return bool(
        connection.execute(
            text("SELECT to_regclass(:table_name) IS NOT NULL"),
            {"table_name": table_name},
        ).scalar_one()
    )
