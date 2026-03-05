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
INCOME_SCORE_HEADER = "Income Score (rate)"
INCOME_RANK_HEADER = "Income Rank (where 1 is most deprived)"
INCOME_DECILE_HEADER = "Income Decile (where 1 is most deprived 10% of LSOAs)"
EMPLOYMENT_SCORE_HEADER = "Employment Score (rate)"
EMPLOYMENT_RANK_HEADER = "Employment Rank (where 1 is most deprived)"
EMPLOYMENT_DECILE_HEADER = "Employment Decile (where 1 is most deprived 10% of LSOAs)"
EDUCATION_SCORE_HEADER = "Education, Skills and Training Score"
EDUCATION_RANK_HEADER = "Education, Skills and Training Rank (where 1 is most deprived)"
EDUCATION_DECILE_HEADER = (
    "Education, Skills and Training Decile (where 1 is most deprived 10% of LSOAs)"
)
HEALTH_SCORE_HEADER = "Health Deprivation and Disability Score"
HEALTH_RANK_HEADER = "Health Deprivation and Disability Rank (where 1 is most deprived)"
HEALTH_DECILE_HEADER = (
    "Health Deprivation and Disability Decile (where 1 is most deprived 10% of LSOAs)"
)
CRIME_SCORE_HEADER = "Crime Score"
CRIME_RANK_HEADER = "Crime Rank (where 1 is most deprived)"
CRIME_DECILE_HEADER = "Crime Decile (where 1 is most deprived 10% of LSOAs)"
BARRIERS_SCORE_HEADER = "Barriers to Housing and Services Score"
BARRIERS_RANK_HEADER = "Barriers to Housing and Services Rank (where 1 is most deprived)"
BARRIERS_DECILE_HEADER = (
    "Barriers to Housing and Services Decile (where 1 is most deprived 10% of LSOAs)"
)
LIVING_ENVIRONMENT_SCORE_HEADER = "Living Environment Score"
LIVING_ENVIRONMENT_RANK_HEADER = "Living Environment Rank (where 1 is most deprived)"
LIVING_ENVIRONMENT_DECILE_HEADER = (
    "Living Environment Decile (where 1 is most deprived 10% of LSOAs)"
)

RELEASE_CONFIG: dict[str, dict[str, str]] = {
    IMD_RELEASE_IOD2025: {
        "source_release_label": "IoD2025",
        "lsoa_vintage": "2021",
        "lsoa_code_header": "LSOA code (2021)",
        "lsoa_name_header": "LSOA name (2021)",
        "lad_code_header": "Local Authority District code (2024)",
        "lad_name_header": "Local Authority District name (2024)",
        "population_total_header": "Total population: mid 2022",
    },
    IMD_RELEASE_IOD2019: {
        "source_release_label": "IoD2019",
        "lsoa_vintage": "2011",
        "lsoa_code_header": "LSOA code (2011)",
        "lsoa_name_header": "LSOA name (2011)",
        "lad_code_header": "Local Authority District code (2019)",
        "lad_name_header": "Local Authority District name (2019)",
        "population_total_header": "Total population: mid 2015 (excluding prisoners)",
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
        INCOME_SCORE_HEADER,
        INCOME_RANK_HEADER,
        INCOME_DECILE_HEADER,
        EMPLOYMENT_SCORE_HEADER,
        EMPLOYMENT_RANK_HEADER,
        EMPLOYMENT_DECILE_HEADER,
        EDUCATION_SCORE_HEADER,
        EDUCATION_RANK_HEADER,
        EDUCATION_DECILE_HEADER,
        HEALTH_SCORE_HEADER,
        HEALTH_RANK_HEADER,
        HEALTH_DECILE_HEADER,
        CRIME_SCORE_HEADER,
        CRIME_RANK_HEADER,
        CRIME_DECILE_HEADER,
        BARRIERS_SCORE_HEADER,
        BARRIERS_RANK_HEADER,
        BARRIERS_DECILE_HEADER,
        LIVING_ENVIRONMENT_SCORE_HEADER,
        LIVING_ENVIRONMENT_RANK_HEADER,
        LIVING_ENVIRONMENT_DECILE_HEADER,
        IDACI_SCORE_HEADER,
        IDACI_RANK_HEADER,
        IDACI_DECILE_HEADER,
        release_config["population_total_header"],
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

    try:
        income_score = parse_required_float(raw_row.get(INCOME_SCORE_HEADER))
    except ValueError:
        return None, "invalid_income_score"

    try:
        income_rank = parse_required_integer(raw_row.get(INCOME_RANK_HEADER))
    except ValueError:
        return None, "invalid_income_rank"

    try:
        income_decile = parse_required_decile(raw_row.get(INCOME_DECILE_HEADER))
    except ValueError:
        return None, "invalid_income_decile"

    try:
        employment_score = parse_required_float(raw_row.get(EMPLOYMENT_SCORE_HEADER))
    except ValueError:
        return None, "invalid_employment_score"

    try:
        employment_rank = parse_required_integer(raw_row.get(EMPLOYMENT_RANK_HEADER))
    except ValueError:
        return None, "invalid_employment_rank"

    try:
        employment_decile = parse_required_decile(raw_row.get(EMPLOYMENT_DECILE_HEADER))
    except ValueError:
        return None, "invalid_employment_decile"

    try:
        education_score = parse_required_float(raw_row.get(EDUCATION_SCORE_HEADER))
    except ValueError:
        return None, "invalid_education_score"

    try:
        education_rank = parse_required_integer(raw_row.get(EDUCATION_RANK_HEADER))
    except ValueError:
        return None, "invalid_education_rank"

    try:
        education_decile = parse_required_decile(raw_row.get(EDUCATION_DECILE_HEADER))
    except ValueError:
        return None, "invalid_education_decile"

    try:
        health_score = parse_required_float(raw_row.get(HEALTH_SCORE_HEADER))
    except ValueError:
        return None, "invalid_health_score"

    try:
        health_rank = parse_required_integer(raw_row.get(HEALTH_RANK_HEADER))
    except ValueError:
        return None, "invalid_health_rank"

    try:
        health_decile = parse_required_decile(raw_row.get(HEALTH_DECILE_HEADER))
    except ValueError:
        return None, "invalid_health_decile"

    try:
        crime_score = parse_required_float(raw_row.get(CRIME_SCORE_HEADER))
    except ValueError:
        return None, "invalid_crime_score"

    try:
        crime_rank = parse_required_integer(raw_row.get(CRIME_RANK_HEADER))
    except ValueError:
        return None, "invalid_crime_rank"

    try:
        crime_decile = parse_required_decile(raw_row.get(CRIME_DECILE_HEADER))
    except ValueError:
        return None, "invalid_crime_decile"

    try:
        barriers_score = parse_required_float(raw_row.get(BARRIERS_SCORE_HEADER))
    except ValueError:
        return None, "invalid_barriers_score"

    try:
        barriers_rank = parse_required_integer(raw_row.get(BARRIERS_RANK_HEADER))
    except ValueError:
        return None, "invalid_barriers_rank"

    try:
        barriers_decile = parse_required_decile(raw_row.get(BARRIERS_DECILE_HEADER))
    except ValueError:
        return None, "invalid_barriers_decile"

    try:
        living_environment_score = parse_required_float(
            raw_row.get(LIVING_ENVIRONMENT_SCORE_HEADER)
        )
    except ValueError:
        return None, "invalid_living_environment_score"

    try:
        living_environment_rank = parse_required_integer(
            raw_row.get(LIVING_ENVIRONMENT_RANK_HEADER)
        )
    except ValueError:
        return None, "invalid_living_environment_rank"

    try:
        living_environment_decile = parse_required_decile(
            raw_row.get(LIVING_ENVIRONMENT_DECILE_HEADER)
        )
    except ValueError:
        return None, "invalid_living_environment_decile"

    try:
        population_total = parse_required_integer(
            raw_row.get(release_config["population_total_header"])
        )
    except ValueError:
        return None, "invalid_population_total"

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
            income_score=income_score,
            income_rank=income_rank,
            income_decile=income_decile,
            employment_score=employment_score,
            employment_rank=employment_rank,
            employment_decile=employment_decile,
            education_score=education_score,
            education_rank=education_rank,
            education_decile=education_decile,
            health_score=health_score,
            health_rank=health_rank,
            health_decile=health_decile,
            crime_score=crime_score,
            crime_rank=crime_rank,
            crime_decile=crime_decile,
            barriers_score=barriers_score,
            barriers_rank=barriers_rank,
            barriers_decile=barriers_decile,
            living_environment_score=living_environment_score,
            living_environment_rank=living_environment_rank,
            living_environment_decile=living_environment_decile,
            population_total=population_total,
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
