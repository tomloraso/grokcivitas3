from __future__ import annotations

import math
from typing import Mapping, Sequence, TypedDict

CONTRACT_VERSION = "ons_imd.v1"

IMD_RELEASE_IOD2025 = "iod2025"
IMD_RELEASE_IOD2019 = "iod2019"
SUPPORTED_RELEASES = (IMD_RELEASE_IOD2025, IMD_RELEASE_IOD2019)

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

RELEASE_CONFIG: dict[str, dict[str, str]] = {
    IMD_RELEASE_IOD2025: {
        "source_release_label": "IoD2025",
        "lsoa_vintage": "2021",
        "lsoa_code_header": "LSOA code (2021)",
        "lsoa_name_header": "LSOA name (2021)",
        "lad_code_header": "Local Authority District code (2024)",
        "lad_name_header": "Local Authority District name (2024)",
    },
    IMD_RELEASE_IOD2019: {
        "source_release_label": "IoD2019",
        "lsoa_vintage": "2011",
        "lsoa_code_header": "LSOA code (2011)",
        "lsoa_name_header": "LSOA name (2011)",
        "lad_code_header": "Local Authority District code (2019)",
        "lad_name_header": "Local Authority District name (2019)",
    },
}


class NormalizedOnsImdRow(TypedDict):
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


def normalize_release(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized in SUPPORTED_RELEASES:
        return normalized
    msg = "Unsupported IMD release. Expected one of: " + ", ".join(sorted(SUPPORTED_RELEASES))
    raise ValueError(msg)


def validate_headers(headers: Sequence[str], *, source_release: str) -> None:
    release = normalize_release(source_release)
    release_config = RELEASE_CONFIG[release]
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


def normalize_row(
    raw_row: Mapping[str, str],
    *,
    source_release: str,
    source_file_url: str,
) -> tuple[NormalizedOnsImdRow | None, str | None]:
    release = normalize_release(source_release)
    release_config = RELEASE_CONFIG[release]

    lsoa_code = strip_or_none(raw_row.get(release_config["lsoa_code_header"]))
    if lsoa_code is None:
        return None, "missing_lsoa_code"

    lsoa_name = strip_or_none(raw_row.get(release_config["lsoa_name_header"]))
    if lsoa_name is None:
        return None, "missing_lsoa_name"

    try:
        imd_score = parse_required_float(raw_row.get(IMD_SCORE_HEADER))
    except ValueError:
        return None, "invalid_imd_score"

    try:
        imd_rank = parse_required_integer(raw_row.get(IMD_RANK_HEADER))
    except ValueError:
        return None, "invalid_imd_rank"

    try:
        imd_decile = parse_required_decile(raw_row.get(IMD_DECILE_HEADER))
    except ValueError:
        return None, "invalid_imd_decile"

    try:
        idaci_score = parse_required_float(raw_row.get(IDACI_SCORE_HEADER))
    except ValueError:
        return None, "invalid_idaci_score"

    try:
        idaci_rank = parse_required_integer(raw_row.get(IDACI_RANK_HEADER))
    except ValueError:
        return None, "invalid_idaci_rank"

    try:
        idaci_decile = parse_required_decile(raw_row.get(IDACI_DECILE_HEADER))
    except ValueError:
        return None, "invalid_idaci_decile"

    return (
        NormalizedOnsImdRow(
            lsoa_code=lsoa_code,
            lsoa_name=lsoa_name,
            local_authority_district_code=strip_or_none(
                raw_row.get(release_config["lad_code_header"])
            ),
            local_authority_district_name=strip_or_none(
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


def strip_or_none(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    return value or None


def parse_required_float(raw_value: str | None) -> float:
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


def parse_required_integer(raw_value: str | None) -> int:
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


def parse_required_decile(raw_value: str | None) -> int:
    parsed = parse_required_integer(raw_value)
    if parsed < 1 or parsed > 10:
        raise ValueError("decile out of range")
    return parsed
