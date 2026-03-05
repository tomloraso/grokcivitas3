from __future__ import annotations

from pathlib import Path

import pytest

from civitas.infrastructure.pipelines.contracts import ons_imd as ons_imd_contract
from civitas.infrastructure.pipelines.ons_imd import (
    IMD_RELEASE_CONFIG,
    IMD_RELEASE_IOD2019,
    IMD_RELEASE_IOD2025,
    normalize_ons_imd_row,
    validate_ons_imd_headers,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "ons_imd"


def _row_2025(**overrides: str) -> dict[str, str]:
    row = {
        "LSOA code (2021)": "E01000001",
        "LSOA name (2021)": "Alpha 001A",
        "Local Authority District code (2024)": "E09000001",
        "Local Authority District name (2024)": "Alpha District",
        ons_imd_contract.IMD_SCORE_HEADER: "25.1",
        ons_imd_contract.IMD_RANK_HEADER: "100",
        ons_imd_contract.IMD_DECILE_HEADER: "1",
        ons_imd_contract.INCOME_SCORE_HEADER: "0.41",
        ons_imd_contract.INCOME_RANK_HEADER: "150",
        ons_imd_contract.INCOME_DECILE_HEADER: "1",
        ons_imd_contract.EMPLOYMENT_SCORE_HEADER: "0.34",
        ons_imd_contract.EMPLOYMENT_RANK_HEADER: "210",
        ons_imd_contract.EMPLOYMENT_DECILE_HEADER: "1",
        ons_imd_contract.EDUCATION_SCORE_HEADER: "18.0",
        ons_imd_contract.EDUCATION_RANK_HEADER: "305",
        ons_imd_contract.EDUCATION_DECILE_HEADER: "2",
        ons_imd_contract.HEALTH_SCORE_HEADER: "0.27",
        ons_imd_contract.HEALTH_RANK_HEADER: "340",
        ons_imd_contract.HEALTH_DECILE_HEADER: "2",
        ons_imd_contract.CRIME_SCORE_HEADER: "0.19",
        ons_imd_contract.CRIME_RANK_HEADER: "450",
        ons_imd_contract.CRIME_DECILE_HEADER: "2",
        ons_imd_contract.BARRIERS_SCORE_HEADER: "23.0",
        ons_imd_contract.BARRIERS_RANK_HEADER: "780",
        ons_imd_contract.BARRIERS_DECILE_HEADER: "3",
        ons_imd_contract.LIVING_ENVIRONMENT_SCORE_HEADER: "16.3",
        ons_imd_contract.LIVING_ENVIRONMENT_RANK_HEADER: "820",
        ons_imd_contract.LIVING_ENVIRONMENT_DECILE_HEADER: "3",
        ons_imd_contract.IDACI_SCORE_HEADER: "0.45",
        ons_imd_contract.IDACI_RANK_HEADER: "120",
        ons_imd_contract.IDACI_DECILE_HEADER: "1",
        ons_imd_contract.RELEASE_CONFIG[IMD_RELEASE_IOD2025]["population_total_header"]: "1820",
    }
    row.update(overrides)
    return row


def _row_2019(**overrides: str) -> dict[str, str]:
    row = {
        "LSOA code (2011)": "E01000003",
        "LSOA name (2011)": "Beta 001A",
        "Local Authority District code (2019)": "E09000002",
        "Local Authority District name (2019)": "Beta District",
        ons_imd_contract.IMD_SCORE_HEADER: "19.8",
        ons_imd_contract.IMD_RANK_HEADER: "540",
        ons_imd_contract.IMD_DECILE_HEADER: "2",
        ons_imd_contract.INCOME_SCORE_HEADER: "0.27",
        ons_imd_contract.INCOME_RANK_HEADER: "550",
        ons_imd_contract.INCOME_DECILE_HEADER: "2",
        ons_imd_contract.EMPLOYMENT_SCORE_HEADER: "0.22",
        ons_imd_contract.EMPLOYMENT_RANK_HEADER: "620",
        ons_imd_contract.EMPLOYMENT_DECILE_HEADER: "2",
        ons_imd_contract.EDUCATION_SCORE_HEADER: "14.2",
        ons_imd_contract.EDUCATION_RANK_HEADER: "740",
        ons_imd_contract.EDUCATION_DECILE_HEADER: "3",
        ons_imd_contract.HEALTH_SCORE_HEADER: "0.17",
        ons_imd_contract.HEALTH_RANK_HEADER: "810",
        ons_imd_contract.HEALTH_DECILE_HEADER: "3",
        ons_imd_contract.CRIME_SCORE_HEADER: "0.14",
        ons_imd_contract.CRIME_RANK_HEADER: "910",
        ons_imd_contract.CRIME_DECILE_HEADER: "3",
        ons_imd_contract.BARRIERS_SCORE_HEADER: "19.4",
        ons_imd_contract.BARRIERS_RANK_HEADER: "1020",
        ons_imd_contract.BARRIERS_DECILE_HEADER: "4",
        ons_imd_contract.LIVING_ENVIRONMENT_SCORE_HEADER: "12.9",
        ons_imd_contract.LIVING_ENVIRONMENT_RANK_HEADER: "1100",
        ons_imd_contract.LIVING_ENVIRONMENT_DECILE_HEADER: "4",
        ons_imd_contract.IDACI_SCORE_HEADER: "0.31",
        ons_imd_contract.IDACI_RANK_HEADER: "700",
        ons_imd_contract.IDACI_DECILE_HEADER: "2",
        ons_imd_contract.RELEASE_CONFIG[IMD_RELEASE_IOD2019]["population_total_header"]: "2100",
    }
    row.update(overrides)
    return row


def test_validate_ons_imd_headers_rejects_missing_2025_field() -> None:
    release_headers = IMD_RELEASE_CONFIG[IMD_RELEASE_IOD2025]
    headers = [
        release_headers["lsoa_code_header"],
        release_headers["lsoa_name_header"],
        release_headers["lad_code_header"],
        release_headers["lad_name_header"],
        ons_imd_contract.IMD_SCORE_HEADER,
        ons_imd_contract.IMD_RANK_HEADER,
        ons_imd_contract.IMD_DECILE_HEADER,
        ons_imd_contract.INCOME_SCORE_HEADER,
        ons_imd_contract.INCOME_RANK_HEADER,
        ons_imd_contract.INCOME_DECILE_HEADER,
        ons_imd_contract.EMPLOYMENT_SCORE_HEADER,
        ons_imd_contract.EMPLOYMENT_RANK_HEADER,
        ons_imd_contract.EMPLOYMENT_DECILE_HEADER,
        ons_imd_contract.EDUCATION_SCORE_HEADER,
        ons_imd_contract.EDUCATION_RANK_HEADER,
        ons_imd_contract.EDUCATION_DECILE_HEADER,
        ons_imd_contract.HEALTH_SCORE_HEADER,
        ons_imd_contract.HEALTH_RANK_HEADER,
        ons_imd_contract.HEALTH_DECILE_HEADER,
        ons_imd_contract.CRIME_SCORE_HEADER,
        ons_imd_contract.CRIME_RANK_HEADER,
        ons_imd_contract.CRIME_DECILE_HEADER,
        ons_imd_contract.BARRIERS_SCORE_HEADER,
        ons_imd_contract.BARRIERS_RANK_HEADER,
        ons_imd_contract.BARRIERS_DECILE_HEADER,
        ons_imd_contract.LIVING_ENVIRONMENT_SCORE_HEADER,
        ons_imd_contract.LIVING_ENVIRONMENT_RANK_HEADER,
        ons_imd_contract.LIVING_ENVIRONMENT_DECILE_HEADER,
        ons_imd_contract.IDACI_SCORE_HEADER,
        ons_imd_contract.IDACI_RANK_HEADER,
        release_headers["population_total_header"],
    ]

    with pytest.raises(ValueError, match="IDACI"):
        validate_ons_imd_headers(headers, source_release=IMD_RELEASE_IOD2025)


def test_validate_ons_imd_headers_accepts_2019_schema() -> None:
    release_headers = IMD_RELEASE_CONFIG[IMD_RELEASE_IOD2019]
    headers = [
        release_headers["lsoa_code_header"],
        release_headers["lsoa_name_header"],
        release_headers["lad_code_header"],
        release_headers["lad_name_header"],
        ons_imd_contract.IMD_SCORE_HEADER,
        ons_imd_contract.IMD_RANK_HEADER,
        ons_imd_contract.IMD_DECILE_HEADER,
        ons_imd_contract.INCOME_SCORE_HEADER,
        ons_imd_contract.INCOME_RANK_HEADER,
        ons_imd_contract.INCOME_DECILE_HEADER,
        ons_imd_contract.EMPLOYMENT_SCORE_HEADER,
        ons_imd_contract.EMPLOYMENT_RANK_HEADER,
        ons_imd_contract.EMPLOYMENT_DECILE_HEADER,
        ons_imd_contract.EDUCATION_SCORE_HEADER,
        ons_imd_contract.EDUCATION_RANK_HEADER,
        ons_imd_contract.EDUCATION_DECILE_HEADER,
        ons_imd_contract.HEALTH_SCORE_HEADER,
        ons_imd_contract.HEALTH_RANK_HEADER,
        ons_imd_contract.HEALTH_DECILE_HEADER,
        ons_imd_contract.CRIME_SCORE_HEADER,
        ons_imd_contract.CRIME_RANK_HEADER,
        ons_imd_contract.CRIME_DECILE_HEADER,
        ons_imd_contract.BARRIERS_SCORE_HEADER,
        ons_imd_contract.BARRIERS_RANK_HEADER,
        ons_imd_contract.BARRIERS_DECILE_HEADER,
        ons_imd_contract.LIVING_ENVIRONMENT_SCORE_HEADER,
        ons_imd_contract.LIVING_ENVIRONMENT_RANK_HEADER,
        ons_imd_contract.LIVING_ENVIRONMENT_DECILE_HEADER,
        ons_imd_contract.IDACI_SCORE_HEADER,
        ons_imd_contract.IDACI_RANK_HEADER,
        ons_imd_contract.IDACI_DECILE_HEADER,
        release_headers["population_total_header"],
    ]

    validate_ons_imd_headers(headers, source_release=IMD_RELEASE_IOD2019)


def test_normalize_ons_imd_row_returns_typed_record_for_valid_input() -> None:
    normalized, rejection = normalize_ons_imd_row(
        _row_2025(),
        source_release=IMD_RELEASE_IOD2025,
        source_file_url="https://example.com/file_7.csv",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.lsoa_code == "E01000001"
    assert normalized.lsoa_name == "Alpha 001A"
    assert normalized.local_authority_district_code == "E09000001"
    assert normalized.imd_score == 25.1
    assert normalized.imd_rank == 100
    assert normalized.imd_decile == 1
    assert normalized.idaci_score == 0.45
    assert normalized.idaci_rank == 120
    assert normalized.idaci_decile == 1
    assert normalized.income_score == 0.41
    assert normalized.employment_score == 0.34
    assert normalized.education_score == 18.0
    assert normalized.health_score == 0.27
    assert normalized.crime_score == 0.19
    assert normalized.barriers_score == 23.0
    assert normalized.living_environment_score == 16.3
    assert normalized.population_total == 1820
    assert normalized.source_release == "IoD2025"
    assert normalized.lsoa_vintage == "2021"


def test_normalize_ons_imd_row_supports_2019_schema_columns() -> None:
    normalized, rejection = normalize_ons_imd_row(
        _row_2019(),
        source_release=IMD_RELEASE_IOD2019,
        source_file_url="https://example.com/file_7_2019.csv",
    )

    assert rejection is None
    assert normalized is not None
    assert normalized.lsoa_code == "E01000003"
    assert normalized.lsoa_name == "Beta 001A"
    assert normalized.local_authority_district_code == "E09000002"
    assert normalized.source_release == "IoD2019"
    assert normalized.lsoa_vintage == "2011"


def test_normalize_ons_imd_row_rejects_missing_lsoa_code() -> None:
    normalized, rejection = normalize_ons_imd_row(
        _row_2025(**{"LSOA code (2021)": ""}),
        source_release=IMD_RELEASE_IOD2025,
        source_file_url="https://example.com/file_7.csv",
    )

    assert normalized is None
    assert rejection == "missing_lsoa_code"


def test_normalize_ons_imd_row_rejects_invalid_decile() -> None:
    normalized, rejection = normalize_ons_imd_row(
        _row_2025(**{ons_imd_contract.IMD_DECILE_HEADER: "11"}),
        source_release=IMD_RELEASE_IOD2025,
        source_file_url="https://example.com/file_7.csv",
    )

    assert normalized is None
    assert rejection == "invalid_imd_decile"


def test_normalize_ons_imd_row_rejects_invalid_idaci_score() -> None:
    normalized, rejection = normalize_ons_imd_row(
        _row_2025(**{ons_imd_contract.IDACI_SCORE_HEADER: "oops"}),
        source_release=IMD_RELEASE_IOD2025,
        source_file_url="https://example.com/file_7.csv",
    )

    assert normalized is None
    assert rejection == "invalid_idaci_score"


def test_ons_imd_fixtures_are_present() -> None:
    assert (FIXTURES_DIR / "file_7_valid_2025.csv").exists()
    assert (FIXTURES_DIR / "file_7_mixed_2025.csv").exists()
