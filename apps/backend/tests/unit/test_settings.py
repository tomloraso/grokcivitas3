from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from civitas.infrastructure.config.settings import (
    DEFAULT_BRONZE_ROOT,
    DEFAULT_DATABASE_URL,
    DEFAULT_DFE_CHARACTERISTICS_DATASET_ID,
    DEFAULT_IMD_RELEASE,
    DEFAULT_OFSTED_TIMELINE_YEARS,
    DEFAULT_POLICE_CRIME_RADIUS_METERS,
    DEFAULT_POLICE_CRIME_SOURCE_MODE,
    DEFAULT_POSTCODE_CACHE_TTL_DAYS,
    DEFAULT_POSTCODES_IO_BASE_URL,
    AppSettings,
    get_settings,
)

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "civitas"
SETTINGS_MODULE_PATH = SRC_ROOT / "infrastructure" / "config" / "settings.py"
ENV_ACCESS_PATTERN = re.compile(r"\bos\.(?:environ|getenv)\b|\benviron\s*\[")


def test_app_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "CIVITAS_DATABASE_URL",
        "CIVITAS_BRONZE_ROOT",
        "CIVITAS_GIAS_SOURCE_CSV",
        "CIVITAS_GIAS_SOURCE_ZIP",
        "CIVITAS_DFE_CHARACTERISTICS_SOURCE_CSV",
        "CIVITAS_DFE_CHARACTERISTICS_DATASET_ID",
        "CIVITAS_IMD_SOURCE_CSV",
        "CIVITAS_IMD_RELEASE",
        "CIVITAS_POLICE_CRIME_SOURCE_ARCHIVE_URL",
        "CIVITAS_POLICE_CRIME_SOURCE_MODE",
        "CIVITAS_POLICE_CRIME_RADIUS_METERS",
        "CIVITAS_OFSTED_LATEST_SOURCE_CSV",
        "CIVITAS_OFSTED_TIMELINE_SOURCE_INDEX_URL",
        "CIVITAS_OFSTED_TIMELINE_SOURCE_ASSETS",
        "CIVITAS_OFSTED_TIMELINE_YEARS",
        "CIVITAS_OFSTED_TIMELINE_INCLUDE_HISTORICAL_BASELINE",
        "CIVITAS_HTTP_TIMEOUT_SECONDS",
        "CIVITAS_HTTP_MAX_RETRIES",
        "CIVITAS_HTTP_RETRY_BACKOFF_SECONDS",
        "CIVITAS_POSTCODES_IO_BASE_URL",
        "CIVITAS_POSTCODE_CACHE_TTL_DAYS",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = AppSettings(_env_file=None)

    assert settings.database.url == DEFAULT_DATABASE_URL
    assert settings.pipeline.bronze_root == DEFAULT_BRONZE_ROOT
    assert settings.pipeline.gias_source_csv is None
    assert settings.pipeline.gias_source_zip is None
    assert settings.pipeline.dfe_characteristics_source_csv is None
    assert settings.pipeline.imd_source_csv is None
    assert settings.pipeline.imd_release == DEFAULT_IMD_RELEASE
    assert settings.pipeline.police_crime_source_archive_url is None
    assert settings.pipeline.police_crime_source_mode == DEFAULT_POLICE_CRIME_SOURCE_MODE
    assert settings.pipeline.police_crime_radius_meters == DEFAULT_POLICE_CRIME_RADIUS_METERS
    assert settings.pipeline.ofsted_latest_source_csv is None
    assert (
        settings.pipeline.ofsted_timeline_source_index_url
        == "https://www.gov.uk/government/statistical-data-sets/"
        "monthly-management-information-ofsteds-school-inspections-outcomes"
    )
    assert settings.pipeline.ofsted_timeline_source_assets is None
    assert settings.pipeline.ofsted_timeline_years == DEFAULT_OFSTED_TIMELINE_YEARS
    assert settings.pipeline.ofsted_timeline_include_historical_baseline is True
    assert (
        settings.pipeline.dfe_characteristics_dataset_id == DEFAULT_DFE_CHARACTERISTICS_DATASET_ID
    )
    assert settings.http_clients.timeout_seconds == 10.0
    assert settings.http_clients.max_retries == 2
    assert settings.http_clients.retry_backoff_seconds == 0.5
    assert settings.school_search.postcodes_io_base_url == DEFAULT_POSTCODES_IO_BASE_URL
    assert settings.school_search.postcode_cache_ttl_days == DEFAULT_POSTCODE_CACHE_TTL_DAYS


def test_app_settings_reads_environment_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(
        "CIVITAS_DATABASE_URL", "postgresql+psycopg://override:override@localhost:5432/app"
    )
    monkeypatch.setenv("CIVITAS_BRONZE_ROOT", str(tmp_path / "custom-bronze"))
    monkeypatch.setenv("CIVITAS_GIAS_SOURCE_CSV", "  https://example.com/gias.csv  ")
    monkeypatch.setenv(
        "CIVITAS_DFE_CHARACTERISTICS_SOURCE_CSV",
        "  https://example.com/dfe_characteristics.csv  ",
    )
    monkeypatch.setenv("CIVITAS_DFE_CHARACTERISTICS_DATASET_ID", " custom-dataset-id ")
    monkeypatch.setenv("CIVITAS_IMD_SOURCE_CSV", "  https://example.com/file_7.csv  ")
    monkeypatch.setenv("CIVITAS_IMD_RELEASE", " IOD2019 ")
    monkeypatch.setenv(
        "CIVITAS_POLICE_CRIME_SOURCE_ARCHIVE_URL",
        "  https://data.police.uk/data/archive/2026-01.zip  ",
    )
    monkeypatch.setenv("CIVITAS_POLICE_CRIME_SOURCE_MODE", " archive ")
    monkeypatch.setenv("CIVITAS_POLICE_CRIME_RADIUS_METERS", "2000")
    monkeypatch.setenv(
        "CIVITAS_OFSTED_LATEST_SOURCE_CSV",
        "  https://example.com/ofsted_latest.csv  ",
    )
    monkeypatch.setenv(
        "CIVITAS_OFSTED_TIMELINE_SOURCE_INDEX_URL",
        "  https://example.com/ofsted_timeline_index  ",
    )
    monkeypatch.setenv(
        "CIVITAS_OFSTED_TIMELINE_SOURCE_ASSETS",
        "  https://example.com/ofsted_ytd.csv, https://example.com/ofsted_historical.csv  ",
    )
    monkeypatch.setenv("CIVITAS_OFSTED_TIMELINE_YEARS", "5")
    monkeypatch.setenv(
        "CIVITAS_OFSTED_TIMELINE_INCLUDE_HISTORICAL_BASELINE",
        "false",
    )
    monkeypatch.setenv("CIVITAS_HTTP_TIMEOUT_SECONDS", "20")
    monkeypatch.setenv("CIVITAS_HTTP_MAX_RETRIES", "5")
    monkeypatch.setenv("CIVITAS_HTTP_RETRY_BACKOFF_SECONDS", "1.25")
    monkeypatch.setenv("CIVITAS_POSTCODES_IO_BASE_URL", "https://postcodes.io")
    monkeypatch.setenv("CIVITAS_POSTCODE_CACHE_TTL_DAYS", "7")

    settings = AppSettings(_env_file=None)

    assert settings.database.url == "postgresql+psycopg://override:override@localhost:5432/app"
    assert settings.pipeline.bronze_root == tmp_path / "custom-bronze"
    assert settings.pipeline.gias_source_csv == "https://example.com/gias.csv"
    assert (
        settings.pipeline.dfe_characteristics_source_csv
        == "https://example.com/dfe_characteristics.csv"
    )
    assert settings.pipeline.dfe_characteristics_dataset_id == "custom-dataset-id"
    assert settings.pipeline.imd_source_csv == "https://example.com/file_7.csv"
    assert settings.pipeline.imd_release == "iod2019"
    assert (
        settings.pipeline.police_crime_source_archive_url
        == "https://data.police.uk/data/archive/2026-01.zip"
    )
    assert settings.pipeline.police_crime_source_mode == "archive"
    assert settings.pipeline.police_crime_radius_meters == 2000.0
    assert settings.pipeline.ofsted_latest_source_csv == "https://example.com/ofsted_latest.csv"
    assert (
        settings.pipeline.ofsted_timeline_source_index_url
        == "https://example.com/ofsted_timeline_index"
    )
    assert (
        settings.pipeline.ofsted_timeline_source_assets
        == "https://example.com/ofsted_ytd.csv, https://example.com/ofsted_historical.csv"
    )
    assert settings.pipeline.ofsted_timeline_years == 5
    assert settings.pipeline.ofsted_timeline_include_historical_baseline is False
    assert settings.http_clients.timeout_seconds == 20.0
    assert settings.http_clients.max_retries == 5
    assert settings.http_clients.retry_backoff_seconds == 1.25
    assert settings.school_search.postcodes_io_base_url == "https://postcodes.io"
    assert settings.school_search.postcode_cache_ttl_days == 7


def test_app_settings_validation_errors_on_invalid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIVITAS_DATABASE_URL", "")
    monkeypatch.setenv("CIVITAS_HTTP_TIMEOUT_SECONDS", "-1")
    monkeypatch.setenv("CIVITAS_POSTCODE_CACHE_TTL_DAYS", "0")
    monkeypatch.setenv("CIVITAS_DFE_CHARACTERISTICS_DATASET_ID", " ")
    monkeypatch.setenv("CIVITAS_IMD_RELEASE", "not-a-release")
    monkeypatch.setenv("CIVITAS_POLICE_CRIME_SOURCE_MODE", "invalid")
    monkeypatch.setenv("CIVITAS_POLICE_CRIME_RADIUS_METERS", "0")
    monkeypatch.setenv("CIVITAS_OFSTED_TIMELINE_YEARS", "0")

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


def test_runtime_env_access_is_restricted_to_settings_module() -> None:
    violations: list[str] = []
    for py_file in SRC_ROOT.rglob("*.py"):
        if py_file == SETTINGS_MODULE_PATH:
            continue
        if ENV_ACCESS_PATTERN.search(py_file.read_text(encoding="utf-8")):
            violations.append(str(py_file))

    assert not violations, (
        "Direct environment access detected outside settings module:\n" + "\n".join(violations)
    )


def test_get_settings_loader_is_cached() -> None:
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
    get_settings.cache_clear()
