from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import shutil
import urllib.parse
import urllib.request
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import PipelineRunContext, PipelineSource, StageResult, chunked
from .contracts import ons_imd as ons_imd_contract

IOD2025_FILE_7_URL = (
    "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/"
    "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
)
IOD2019_FILE_7_URL = (
    "https://assets.publishing.service.gov.uk/media/5dc407b440f0b6379a7acc8d/"
    "File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv"
)

IMD_RELEASE_IOD2025 = ons_imd_contract.IMD_RELEASE_IOD2025
IMD_RELEASE_IOD2019 = ons_imd_contract.IMD_RELEASE_IOD2019
SUPPORTED_IMD_RELEASES = ons_imd_contract.SUPPORTED_RELEASES

IMD_SCORE_HEADER = ons_imd_contract.IMD_SCORE_HEADER
IMD_RANK_HEADER = ons_imd_contract.IMD_RANK_HEADER
IMD_DECILE_HEADER = ons_imd_contract.IMD_DECILE_HEADER
IDACI_SCORE_HEADER = ons_imd_contract.IDACI_SCORE_HEADER
IDACI_RANK_HEADER = ons_imd_contract.IDACI_RANK_HEADER
IDACI_DECILE_HEADER = ons_imd_contract.IDACI_DECILE_HEADER

IMD_RELEASE_CONFIG: dict[str, dict[str, str]] = {
    IMD_RELEASE_IOD2025: {
        "source_file_url": IOD2025_FILE_7_URL,
        **ons_imd_contract.RELEASE_CONFIG[IMD_RELEASE_IOD2025],
    },
    IMD_RELEASE_IOD2019: {
        "source_file_url": IOD2019_FILE_7_URL,
        **ons_imd_contract.RELEASE_CONFIG[IMD_RELEASE_IOD2019],
    },
}

BRONZE_FILE_NAME = "file_7.csv"
BRONZE_METADATA_FILE_NAME = "file_7.metadata.json"
ONS_IMD_NORMALIZATION_CONTRACT_VERSION = ons_imd_contract.CONTRACT_VERSION


@dataclass(frozen=True)
class OnsImdStagedRow:
    lsoa_code: str
    lsoa_name: str
    local_authority_district_code: str | None
    local_authority_district_name: str | None
    imd_score: float
    imd_rank: int
    imd_decile: int
    idaci_score: float
    idaci_rank: int
    idaci_decile: int
    income_score: float
    income_rank: int
    income_decile: int
    employment_score: float
    employment_rank: int
    employment_decile: int
    education_score: float
    education_rank: int
    education_decile: int
    health_score: float
    health_rank: int
    health_decile: int
    crime_score: float
    crime_rank: int
    crime_decile: int
    barriers_score: float
    barriers_rank: int
    barriers_decile: int
    living_environment_score: float
    living_environment_rank: int
    living_environment_decile: int
    population_total: int
    source_release: str
    lsoa_vintage: str
    source_file_url: str


def validate_ons_imd_headers(headers: Sequence[str], *, source_release: str) -> None:
    ons_imd_contract.validate_headers(headers, source_release=source_release)


def normalize_ons_imd_row(
    raw_row: Mapping[str, str],
    *,
    source_release: str,
    source_file_url: str,
) -> tuple[OnsImdStagedRow | None, str | None]:
    normalized_row, rejection = ons_imd_contract.normalize_row(
        raw_row,
        source_release=source_release,
        source_file_url=source_file_url,
    )
    if normalized_row is None:
        return None, rejection
    return (
        OnsImdStagedRow(
            lsoa_code=normalized_row["lsoa_code"],
            lsoa_name=normalized_row["lsoa_name"],
            local_authority_district_code=normalized_row["local_authority_district_code"],
            local_authority_district_name=normalized_row["local_authority_district_name"],
            imd_score=normalized_row["imd_score"],
            imd_rank=normalized_row["imd_rank"],
            imd_decile=normalized_row["imd_decile"],
            idaci_score=normalized_row["idaci_score"],
            idaci_rank=normalized_row["idaci_rank"],
            idaci_decile=normalized_row["idaci_decile"],
            income_score=normalized_row["income_score"],
            income_rank=normalized_row["income_rank"],
            income_decile=normalized_row["income_decile"],
            employment_score=normalized_row["employment_score"],
            employment_rank=normalized_row["employment_rank"],
            employment_decile=normalized_row["employment_decile"],
            education_score=normalized_row["education_score"],
            education_rank=normalized_row["education_rank"],
            education_decile=normalized_row["education_decile"],
            health_score=normalized_row["health_score"],
            health_rank=normalized_row["health_rank"],
            health_decile=normalized_row["health_decile"],
            crime_score=normalized_row["crime_score"],
            crime_rank=normalized_row["crime_rank"],
            crime_decile=normalized_row["crime_decile"],
            barriers_score=normalized_row["barriers_score"],
            barriers_rank=normalized_row["barriers_rank"],
            barriers_decile=normalized_row["barriers_decile"],
            living_environment_score=normalized_row["living_environment_score"],
            living_environment_rank=normalized_row["living_environment_rank"],
            living_environment_decile=normalized_row["living_environment_decile"],
            population_total=normalized_row["population_total"],
            source_release=normalized_row["source_release"],
            lsoa_vintage=normalized_row["lsoa_vintage"],
            source_file_url=normalized_row["source_file_url"],
        ),
        None,
    )


class OnsImdPipeline:
    source = PipelineSource.ONS_IMD

    def __init__(
        self,
        engine: Engine,
        *,
        source_csv: str | None = None,
        source_release: str = IMD_RELEASE_IOD2025,
    ) -> None:
        self._engine = engine
        self._source_csv = source_csv
        self._source_release = _normalize_release(source_release)

    def download(self, context: PipelineRunContext) -> int:
        context.bronze_source_path.mkdir(parents=True, exist_ok=True)

        target_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if target_csv.exists():
            return _count_csv_rows(target_csv)

        release_config = IMD_RELEASE_CONFIG[self._source_release]
        source_file_url = release_config["source_file_url"]
        if self._source_csv:
            _copy_from_source(self._source_csv, target_csv)
            source_file_url = self._source_csv
        else:
            csv_text = _download_text(source_file_url)
            target_csv.write_text(csv_text, encoding="utf-8")

        row_count = _count_csv_rows(target_csv)
        metadata = {
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "source_file_url": source_file_url,
            "source_release": self._source_release,
            "source_release_label": release_config["source_release_label"],
            "lsoa_vintage": release_config["lsoa_vintage"],
            "normalization_contract_version": ONS_IMD_NORMALIZATION_CONTRACT_VERSION,
            "sha256": _sha256_file(target_csv),
            "rows": row_count,
        }
        metadata_path = context.bronze_source_path / BRONZE_METADATA_FILE_NAME
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        return row_count

    def stage(self, context: PipelineRunContext) -> StageResult:
        source_csv = context.bronze_source_path / BRONZE_FILE_NAME
        if not source_csv.exists():
            raise FileNotFoundError(
                f"ONS IMD bronze file not found at '{source_csv}'. Run download stage first."
            )

        metadata = _load_download_metadata(context.bronze_source_path / BRONZE_METADATA_FILE_NAME)
        source_release = _normalize_release(
            str(metadata.get("source_release"))
            if metadata.get("source_release")
            else self._source_release
        )
        source_file_url = (
            str(metadata.get("source_file_url"))
            if isinstance(metadata.get("source_file_url"), str)
            else IMD_RELEASE_CONFIG[source_release]["source_file_url"]
        )

        staged_rows_by_lsoa: dict[str, OnsImdStagedRow] = {}
        rejected_rows: list[tuple[str, dict[str, str]]] = []
        with source_csv.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise ValueError("ONS IMD CSV has no header row.")
            validate_ons_imd_headers(reader.fieldnames, source_release=source_release)

            for raw_row in reader:
                normalized, rejection = normalize_ons_imd_row(
                    raw_row,
                    source_release=source_release,
                    source_file_url=source_file_url,
                )
                if normalized is not None:
                    staged_rows_by_lsoa[normalized.lsoa_code] = normalized
                    continue
                if rejection is not None:
                    rejected_rows.append((rejection, dict(raw_row)))

        staged_rows = list(staged_rows_by_lsoa.values())
        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            connection.execute(text(f"DROP TABLE IF EXISTS staging.{staging_table_name}"))
            connection.execute(
                text(
                    f"""
                    CREATE TABLE staging.{staging_table_name} (
                        lsoa_code text PRIMARY KEY,
                        lsoa_name text NOT NULL,
                        local_authority_district_code text NULL,
                        local_authority_district_name text NULL,
                        imd_score double precision NOT NULL,
                        imd_rank integer NOT NULL,
                        imd_decile integer NOT NULL,
                        idaci_score double precision NOT NULL,
                        idaci_rank integer NOT NULL,
                        idaci_decile integer NOT NULL,
                        income_score double precision NOT NULL,
                        income_rank integer NOT NULL,
                        income_decile integer NOT NULL,
                        employment_score double precision NOT NULL,
                        employment_rank integer NOT NULL,
                        employment_decile integer NOT NULL,
                        education_score double precision NOT NULL,
                        education_rank integer NOT NULL,
                        education_decile integer NOT NULL,
                        health_score double precision NOT NULL,
                        health_rank integer NOT NULL,
                        health_decile integer NOT NULL,
                        crime_score double precision NOT NULL,
                        crime_rank integer NOT NULL,
                        crime_decile integer NOT NULL,
                        barriers_score double precision NOT NULL,
                        barriers_rank integer NOT NULL,
                        barriers_decile integer NOT NULL,
                        living_environment_score double precision NOT NULL,
                        living_environment_rank integer NOT NULL,
                        living_environment_decile integer NOT NULL,
                        population_total integer NOT NULL,
                        source_release text NOT NULL,
                        lsoa_vintage text NOT NULL,
                        source_file_url text NOT NULL
                    )
                    """
                )
            )

            if staged_rows:
                staged_insert = text(
                    f"""
                    INSERT INTO staging.{staging_table_name} (
                        lsoa_code,
                        lsoa_name,
                        local_authority_district_code,
                        local_authority_district_name,
                        imd_score,
                        imd_rank,
                        imd_decile,
                        idaci_score,
                        idaci_rank,
                        idaci_decile,
                        income_score,
                        income_rank,
                        income_decile,
                        employment_score,
                        employment_rank,
                        employment_decile,
                        education_score,
                        education_rank,
                        education_decile,
                        health_score,
                        health_rank,
                        health_decile,
                        crime_score,
                        crime_rank,
                        crime_decile,
                        barriers_score,
                        barriers_rank,
                        barriers_decile,
                        living_environment_score,
                        living_environment_rank,
                        living_environment_decile,
                        population_total,
                        source_release,
                        lsoa_vintage,
                        source_file_url
                    ) VALUES (
                        :lsoa_code,
                        :lsoa_name,
                        :local_authority_district_code,
                        :local_authority_district_name,
                        :imd_score,
                        :imd_rank,
                        :imd_decile,
                        :idaci_score,
                        :idaci_rank,
                        :idaci_decile,
                        :income_score,
                        :income_rank,
                        :income_decile,
                        :employment_score,
                        :employment_rank,
                        :employment_decile,
                        :education_score,
                        :education_rank,
                        :education_decile,
                        :health_score,
                        :health_rank,
                        :health_decile,
                        :crime_score,
                        :crime_rank,
                        :crime_decile,
                        :barriers_score,
                        :barriers_rank,
                        :barriers_decile,
                        :living_environment_score,
                        :living_environment_rank,
                        :living_environment_decile,
                        :population_total,
                        :source_release,
                        :lsoa_vintage,
                        :source_file_url
                    )
                    ON CONFLICT (lsoa_code) DO UPDATE SET
                        lsoa_name = EXCLUDED.lsoa_name,
                        local_authority_district_code = EXCLUDED.local_authority_district_code,
                        local_authority_district_name = EXCLUDED.local_authority_district_name,
                        imd_score = EXCLUDED.imd_score,
                        imd_rank = EXCLUDED.imd_rank,
                        imd_decile = EXCLUDED.imd_decile,
                        idaci_score = EXCLUDED.idaci_score,
                        idaci_rank = EXCLUDED.idaci_rank,
                        idaci_decile = EXCLUDED.idaci_decile,
                        income_score = EXCLUDED.income_score,
                        income_rank = EXCLUDED.income_rank,
                        income_decile = EXCLUDED.income_decile,
                        employment_score = EXCLUDED.employment_score,
                        employment_rank = EXCLUDED.employment_rank,
                        employment_decile = EXCLUDED.employment_decile,
                        education_score = EXCLUDED.education_score,
                        education_rank = EXCLUDED.education_rank,
                        education_decile = EXCLUDED.education_decile,
                        health_score = EXCLUDED.health_score,
                        health_rank = EXCLUDED.health_rank,
                        health_decile = EXCLUDED.health_decile,
                        crime_score = EXCLUDED.crime_score,
                        crime_rank = EXCLUDED.crime_rank,
                        crime_decile = EXCLUDED.crime_decile,
                        barriers_score = EXCLUDED.barriers_score,
                        barriers_rank = EXCLUDED.barriers_rank,
                        barriers_decile = EXCLUDED.barriers_decile,
                        living_environment_score = EXCLUDED.living_environment_score,
                        living_environment_rank = EXCLUDED.living_environment_rank,
                        living_environment_decile = EXCLUDED.living_environment_decile,
                        population_total = EXCLUDED.population_total,
                        source_release = EXCLUDED.source_release,
                        lsoa_vintage = EXCLUDED.lsoa_vintage,
                        source_file_url = EXCLUDED.source_file_url
                    """
                )
                for rows_chunk in chunked(staged_rows, context.stage_chunk_size):
                    connection.execute(
                        staged_insert,
                        [
                            {
                                "lsoa_code": row.lsoa_code,
                                "lsoa_name": row.lsoa_name,
                                "local_authority_district_code": row.local_authority_district_code,
                                "local_authority_district_name": row.local_authority_district_name,
                                "imd_score": row.imd_score,
                                "imd_rank": row.imd_rank,
                                "imd_decile": row.imd_decile,
                                "idaci_score": row.idaci_score,
                                "idaci_rank": row.idaci_rank,
                                "idaci_decile": row.idaci_decile,
                                "income_score": row.income_score,
                                "income_rank": row.income_rank,
                                "income_decile": row.income_decile,
                                "employment_score": row.employment_score,
                                "employment_rank": row.employment_rank,
                                "employment_decile": row.employment_decile,
                                "education_score": row.education_score,
                                "education_rank": row.education_rank,
                                "education_decile": row.education_decile,
                                "health_score": row.health_score,
                                "health_rank": row.health_rank,
                                "health_decile": row.health_decile,
                                "crime_score": row.crime_score,
                                "crime_rank": row.crime_rank,
                                "crime_decile": row.crime_decile,
                                "barriers_score": row.barriers_score,
                                "barriers_rank": row.barriers_rank,
                                "barriers_decile": row.barriers_decile,
                                "living_environment_score": row.living_environment_score,
                                "living_environment_rank": row.living_environment_rank,
                                "living_environment_decile": row.living_environment_decile,
                                "population_total": row.population_total,
                                "source_release": row.source_release,
                                "lsoa_vintage": row.lsoa_vintage,
                                "source_file_url": row.source_file_url,
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

        return StageResult(
            staged_rows=len(staged_rows),
            rejected_rows=len(rejected_rows),
            contract_version=ONS_IMD_NORMALIZATION_CONTRACT_VERSION,
        )

    def promote(self, context: PipelineRunContext) -> int:
        staging_table_name = self._staging_table_name(context)
        with self._engine.begin() as connection:
            promoted_rows = int(
                connection.execute(
                    text(
                        f"""
                        WITH upserted AS (
                            INSERT INTO area_deprivation (
                                lsoa_code,
                                lsoa_name,
                                local_authority_district_code,
                                local_authority_district_name,
                                imd_score,
                                imd_rank,
                                imd_decile,
                                idaci_score,
                                idaci_rank,
                                idaci_decile,
                                income_score,
                                income_rank,
                                income_decile,
                                employment_score,
                                employment_rank,
                                employment_decile,
                                education_score,
                                education_rank,
                                education_decile,
                                health_score,
                                health_rank,
                                health_decile,
                                crime_score,
                                crime_rank,
                                crime_decile,
                                barriers_score,
                                barriers_rank,
                                barriers_decile,
                                living_environment_score,
                                living_environment_rank,
                                living_environment_decile,
                                population_total,
                                source_release,
                                lsoa_vintage,
                                source_file_url,
                                updated_at
                            )
                            SELECT
                                staged.lsoa_code,
                                staged.lsoa_name,
                                staged.local_authority_district_code,
                                staged.local_authority_district_name,
                                staged.imd_score,
                                staged.imd_rank,
                                staged.imd_decile,
                                staged.idaci_score,
                                staged.idaci_rank,
                                staged.idaci_decile,
                                staged.income_score,
                                staged.income_rank,
                                staged.income_decile,
                                staged.employment_score,
                                staged.employment_rank,
                                staged.employment_decile,
                                staged.education_score,
                                staged.education_rank,
                                staged.education_decile,
                                staged.health_score,
                                staged.health_rank,
                                staged.health_decile,
                                staged.crime_score,
                                staged.crime_rank,
                                staged.crime_decile,
                                staged.barriers_score,
                                staged.barriers_rank,
                                staged.barriers_decile,
                                staged.living_environment_score,
                                staged.living_environment_rank,
                                staged.living_environment_decile,
                                staged.population_total,
                                staged.source_release,
                                staged.lsoa_vintage,
                                staged.source_file_url,
                                timezone('utc', now())
                            FROM staging.{staging_table_name} AS staged
                            ON CONFLICT (lsoa_code) DO UPDATE SET
                                lsoa_name = EXCLUDED.lsoa_name,
                                local_authority_district_code = EXCLUDED.local_authority_district_code,
                                local_authority_district_name = EXCLUDED.local_authority_district_name,
                                imd_score = EXCLUDED.imd_score,
                                imd_rank = EXCLUDED.imd_rank,
                                imd_decile = EXCLUDED.imd_decile,
                                idaci_score = EXCLUDED.idaci_score,
                                idaci_rank = EXCLUDED.idaci_rank,
                                idaci_decile = EXCLUDED.idaci_decile,
                                income_score = EXCLUDED.income_score,
                                income_rank = EXCLUDED.income_rank,
                                income_decile = EXCLUDED.income_decile,
                                employment_score = EXCLUDED.employment_score,
                                employment_rank = EXCLUDED.employment_rank,
                                employment_decile = EXCLUDED.employment_decile,
                                education_score = EXCLUDED.education_score,
                                education_rank = EXCLUDED.education_rank,
                                education_decile = EXCLUDED.education_decile,
                                health_score = EXCLUDED.health_score,
                                health_rank = EXCLUDED.health_rank,
                                health_decile = EXCLUDED.health_decile,
                                crime_score = EXCLUDED.crime_score,
                                crime_rank = EXCLUDED.crime_rank,
                                crime_decile = EXCLUDED.crime_decile,
                                barriers_score = EXCLUDED.barriers_score,
                                barriers_rank = EXCLUDED.barriers_rank,
                                barriers_decile = EXCLUDED.barriers_decile,
                                living_environment_score = EXCLUDED.living_environment_score,
                                living_environment_rank = EXCLUDED.living_environment_rank,
                                living_environment_decile = EXCLUDED.living_environment_decile,
                                population_total = EXCLUDED.population_total,
                                source_release = EXCLUDED.source_release,
                                lsoa_vintage = EXCLUDED.lsoa_vintage,
                                source_file_url = EXCLUDED.source_file_url,
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
        return f"ons_imd__{context.run_id.hex}"


def _normalize_release(value: str) -> str:
    return ons_imd_contract.normalize_release(value)


def _strip_or_none(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    return value or None


def _parse_required_float(raw_value: str | None) -> float:
    value = (raw_value or "").strip()
    if not value:
        raise ValueError("missing float")
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError("invalid float") from exc
    if not math.isfinite(parsed):
        raise ValueError("non-finite float")
    return parsed


def _parse_required_integer(raw_value: str | None) -> int:
    value = (raw_value or "").strip()
    if not value:
        raise ValueError("missing integer")
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError("invalid integer") from exc
    if not math.isfinite(parsed):
        raise ValueError("non-finite integer")
    if not parsed.is_integer():
        raise ValueError("non-integer numeric")
    return int(parsed)


def _parse_required_decile(raw_value: str | None) -> int:
    parsed = _parse_required_integer(raw_value)
    if parsed < 1 or parsed > 10:
        raise ValueError("decile out of range")
    return parsed


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        row_count_with_header = sum(1 for _ in csv.reader(csv_file))
    return max(0, row_count_with_header - 1)


def _decode_response_bytes(raw_bytes: bytes, content_encoding: str | None) -> str:
    encoding_value = (content_encoding or "").casefold()
    should_try_gzip = "gzip" in encoding_value or raw_bytes.startswith(b"\x1f\x8b")
    if should_try_gzip:
        with suppress(OSError):
            raw_bytes = gzip.decompress(raw_bytes)
    return raw_bytes.decode("utf-8-sig", errors="replace")


def _download_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "civitas-pipeline/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw_bytes = response.read()
        return _decode_response_bytes(raw_bytes, response.headers.get("Content-Encoding"))


def _copy_from_source(source: str, target: Path) -> None:
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        request = urllib.request.Request(source, headers={"User-Agent": "civitas-pipeline/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response:
            raw_bytes = response.read()
            text_content = _decode_response_bytes(
                raw_bytes, response.headers.get("Content-Encoding")
            )
            target.write_text(text_content, encoding="utf-8")
        return

    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(
            f"Configured ONS IMD source CSV path '{source_path}' was not found."
        )
    shutil.copy2(source_path, target)


def _load_download_metadata(metadata_path: Path) -> dict[str, object]:
    if not metadata_path.exists():
        return {}
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
