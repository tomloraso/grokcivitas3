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

from .base import PipelineRunContext, PipelineSource, StageResult

IOD2025_FILE_7_URL = (
    "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/"
    "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
)
IOD2019_FILE_7_URL = (
    "https://assets.publishing.service.gov.uk/media/5dc407b440f0b6379a7acc8d/"
    "File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv"
)

IMD_RELEASE_IOD2025 = "iod2025"
IMD_RELEASE_IOD2019 = "iod2019"
SUPPORTED_IMD_RELEASES = (IMD_RELEASE_IOD2025, IMD_RELEASE_IOD2019)

IMD_SCORE_HEADER = "Index of Multiple Deprivation (IMD) Score"
IMD_RANK_HEADER = "Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)"
IMD_DECILE_HEADER = (
    "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)"
)
IDACI_SCORE_HEADER = "Income Deprivation Affecting Children Index (IDACI) Score (rate)"
IDACI_RANK_HEADER = (
    "Income Deprivation Affecting Children Index (IDACI) Rank (where 1 is most deprived)"
)
IDACI_DECILE_HEADER = (
    "Income Deprivation Affecting Children Index (IDACI) Decile "
    "(where 1 is most deprived 10% of LSOAs)"
)

IMD_RELEASE_CONFIG: dict[str, dict[str, str]] = {
    IMD_RELEASE_IOD2025: {
        "source_file_url": IOD2025_FILE_7_URL,
        "source_release_label": "IoD2025",
        "lsoa_vintage": "2021",
        "lsoa_code_header": "LSOA code (2021)",
        "lsoa_name_header": "LSOA name (2021)",
        "lad_code_header": "Local Authority District code (2024)",
        "lad_name_header": "Local Authority District name (2024)",
    },
    IMD_RELEASE_IOD2019: {
        "source_file_url": IOD2019_FILE_7_URL,
        "source_release_label": "IoD2019",
        "lsoa_vintage": "2011",
        "lsoa_code_header": "LSOA code (2011)",
        "lsoa_name_header": "LSOA name (2011)",
        "lad_code_header": "Local Authority District code (2019)",
        "lad_name_header": "Local Authority District name (2019)",
    },
}

BRONZE_FILE_NAME = "file_7.csv"
BRONZE_METADATA_FILE_NAME = "file_7.metadata.json"


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
    source_release: str
    lsoa_vintage: str
    source_file_url: str


def validate_ons_imd_headers(headers: Sequence[str], *, source_release: str) -> None:
    release = _normalize_release(source_release)
    release_config = IMD_RELEASE_CONFIG[release]
    required_headers = [
        release_config["lsoa_code_header"],
        release_config["lsoa_name_header"],
        release_config["lad_code_header"],
        release_config["lad_name_header"],
        IMD_SCORE_HEADER,
        IMD_RANK_HEADER,
        IMD_DECILE_HEADER,
        IDACI_SCORE_HEADER,
        IDACI_RANK_HEADER,
        IDACI_DECILE_HEADER,
    ]
    header_set = set(headers)
    missing = [header for header in required_headers if header not in header_set]
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(
            f"ONS IMD schema mismatch for '{release}'; missing required headers: {missing_fields}"
        )


def normalize_ons_imd_row(
    raw_row: Mapping[str, str],
    *,
    source_release: str,
    source_file_url: str,
) -> tuple[OnsImdStagedRow | None, str | None]:
    release = _normalize_release(source_release)
    release_config = IMD_RELEASE_CONFIG[release]

    lsoa_code = _strip_or_none(raw_row.get(release_config["lsoa_code_header"]))
    if lsoa_code is None:
        return None, "missing_lsoa_code"

    lsoa_name = _strip_or_none(raw_row.get(release_config["lsoa_name_header"]))
    if lsoa_name is None:
        return None, "missing_lsoa_name"

    try:
        imd_score = _parse_required_float(raw_row.get(IMD_SCORE_HEADER))
    except ValueError:
        return None, "invalid_imd_score"

    try:
        imd_rank = _parse_required_integer(raw_row.get(IMD_RANK_HEADER))
    except ValueError:
        return None, "invalid_imd_rank"

    try:
        imd_decile = _parse_required_decile(raw_row.get(IMD_DECILE_HEADER))
    except ValueError:
        return None, "invalid_imd_decile"

    try:
        idaci_score = _parse_required_float(raw_row.get(IDACI_SCORE_HEADER))
    except ValueError:
        return None, "invalid_idaci_score"

    try:
        idaci_rank = _parse_required_integer(raw_row.get(IDACI_RANK_HEADER))
    except ValueError:
        return None, "invalid_idaci_rank"

    try:
        idaci_decile = _parse_required_decile(raw_row.get(IDACI_DECILE_HEADER))
    except ValueError:
        return None, "invalid_idaci_decile"

    return (
        OnsImdStagedRow(
            lsoa_code=lsoa_code,
            lsoa_name=lsoa_name,
            local_authority_district_code=_strip_or_none(
                raw_row.get(release_config["lad_code_header"])
            ),
            local_authority_district_name=_strip_or_none(
                raw_row.get(release_config["lad_name_header"])
            ),
            imd_score=imd_score,
            imd_rank=imd_rank,
            imd_decile=imd_decile,
            idaci_score=idaci_score,
            idaci_rank=idaci_rank,
            idaci_decile=idaci_decile,
            source_release=release_config["source_release_label"],
            lsoa_vintage=release_config["lsoa_vintage"],
            source_file_url=source_file_url,
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
                        source_release text NOT NULL,
                        lsoa_vintage text NOT NULL,
                        source_file_url text NOT NULL
                    )
                    """
                )
            )

            if staged_rows:
                connection.execute(
                    text(
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
                            source_release = EXCLUDED.source_release,
                            lsoa_vintage = EXCLUDED.lsoa_vintage,
                            source_file_url = EXCLUDED.source_file_url
                        """
                    ),
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
                            "source_release": row.source_release,
                            "lsoa_vintage": row.lsoa_vintage,
                            "source_file_url": row.source_file_url,
                        }
                        for row in staged_rows
                    ],
                )

            if rejected_rows:
                connection.execute(
                    text(
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
                    ),
                    [
                        {
                            "run_id": str(context.run_id),
                            "source": context.source.value,
                            "reason_code": reason_code,
                            "raw_record": json.dumps(raw_row, ensure_ascii=True),
                        }
                        for reason_code, raw_row in rejected_rows
                    ],
                )

        return StageResult(staged_rows=len(staged_rows), rejected_rows=len(rejected_rows))

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
    normalized = value.strip().casefold()
    if normalized in SUPPORTED_IMD_RELEASES:
        return normalized
    if normalized == "iod2025":
        return IMD_RELEASE_IOD2025
    if normalized == "iod2019":
        return IMD_RELEASE_IOD2019
    msg = "Unsupported IMD release. Expected one of: " + ", ".join(sorted(SUPPORTED_IMD_RELEASES))
    raise ValueError(msg)


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
