from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from civitas.infrastructure.config.settings import (
    DEFAULT_BRONZE_ROOT,
    DEFAULT_DATA_QUALITY_COVERAGE_DRIFT_THRESHOLD,
    DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
    DEFAULT_DATA_QUALITY_MAX_CONSECUTIVE_HARD_FAILURES,
    DEFAULT_DATA_QUALITY_SPARSE_TREND_RATIO_THRESHOLD,
    DEFAULT_DATABASE_URL,
    DEFAULT_DEMOGRAPHICS_LOOKBACK_YEARS,
    DEFAULT_DEMOGRAPHICS_RELEASE_SLUGS,
    DEFAULT_DEMOGRAPHICS_SEN_PUBLICATION_SLUG,
    DEFAULT_DEMOGRAPHICS_SOURCE_MODE,
    DEFAULT_DEMOGRAPHICS_SPC_PUBLICATION_SLUG,
    DEFAULT_IMD_RELEASE,
    DEFAULT_OFSTED_TIMELINE_YEARS,
    DEFAULT_PIPELINE_HTTP_TIMEOUT_SECONDS,
    DEFAULT_PIPELINE_MAX_CONCURRENT_SOURCES,
    DEFAULT_PIPELINE_MAX_RETRIES,
    DEFAULT_PIPELINE_PROMOTE_CHUNK_SIZE,
    DEFAULT_PIPELINE_RESUME_ENABLED,
    DEFAULT_PIPELINE_RETRY_BACKOFF_SECONDS,
    DEFAULT_PIPELINE_STAGE_CHUNK_SIZE,
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
        "CIVITAS_DEMOGRAPHICS_SOURCE_MODE",
        "CIVITAS_DEMOGRAPHICS_SPC_PUBLICATION_SLUG",
        "CIVITAS_DEMOGRAPHICS_SEN_PUBLICATION_SLUG",
        "CIVITAS_DEMOGRAPHICS_RELEASE_SLUGS",
        "CIVITAS_DEMOGRAPHICS_LOOKBACK_YEARS",
        "CIVITAS_DEMOGRAPHICS_SOURCE_STRICT_MODE",
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
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_GIAS",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_CHARACTERISTICS",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_OFSTED_LATEST",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_OFSTED_TIMELINE",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_ONS_IMD",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_POLICE_CRIME_CONTEXT",
        "CIVITAS_PIPELINE_HTTP_TIMEOUT_SECONDS",
        "CIVITAS_PIPELINE_MAX_RETRIES",
        "CIVITAS_PIPELINE_RETRY_BACKOFF_SECONDS",
        "CIVITAS_PIPELINE_STAGE_CHUNK_SIZE",
        "CIVITAS_PIPELINE_PROMOTE_CHUNK_SIZE",
        "CIVITAS_PIPELINE_MAX_CONCURRENT_SOURCES",
        "CIVITAS_PIPELINE_RESUME_ENABLED",
        "CIVITAS_HTTP_TIMEOUT_SECONDS",
        "CIVITAS_HTTP_MAX_RETRIES",
        "CIVITAS_HTTP_RETRY_BACKOFF_SECONDS",
        "CIVITAS_POSTCODES_IO_BASE_URL",
        "CIVITAS_POSTCODE_CACHE_TTL_DAYS",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_GIAS",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_CHARACTERISTICS",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_OFSTED_LATEST",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_OFSTED_TIMELINE",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_ONS_IMD",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_POLICE_CRIME_CONTEXT",
        "CIVITAS_DATA_QUALITY_COVERAGE_DRIFT_THRESHOLD",
        "CIVITAS_DATA_QUALITY_MAX_CONSECUTIVE_HARD_FAILURES",
        "CIVITAS_DATA_QUALITY_SPARSE_TREND_RATIO_THRESHOLD",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = AppSettings(_env_file=None)

    assert settings.database.url == DEFAULT_DATABASE_URL
    assert settings.pipeline.bronze_root == DEFAULT_BRONZE_ROOT
    assert settings.pipeline.gias_source_csv is None
    assert settings.pipeline.gias_source_zip is None
    assert settings.pipeline.demographics_source_mode == DEFAULT_DEMOGRAPHICS_SOURCE_MODE
    assert (
        settings.pipeline.demographics_spc_publication_slug
        == DEFAULT_DEMOGRAPHICS_SPC_PUBLICATION_SLUG
    )
    assert (
        settings.pipeline.demographics_sen_publication_slug
        == DEFAULT_DEMOGRAPHICS_SEN_PUBLICATION_SLUG
    )
    assert settings.pipeline.demographics_release_slugs == DEFAULT_DEMOGRAPHICS_RELEASE_SLUGS
    assert settings.pipeline.demographics_lookback_years == DEFAULT_DEMOGRAPHICS_LOOKBACK_YEARS
    assert settings.pipeline.demographics_source_strict_mode is True
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
    assert settings.pipeline.max_reject_ratio_gias == 1.0
    assert settings.pipeline.max_reject_ratio_dfe_characteristics == 1.0
    assert settings.pipeline.max_reject_ratio_ofsted_latest == 1.0
    assert settings.pipeline.max_reject_ratio_ofsted_timeline == 1.0
    assert settings.pipeline.max_reject_ratio_ons_imd == 1.0
    assert settings.pipeline.max_reject_ratio_police_crime_context == 1.0
    assert settings.pipeline.http_timeout_seconds == DEFAULT_PIPELINE_HTTP_TIMEOUT_SECONDS
    assert settings.pipeline.max_retries == DEFAULT_PIPELINE_MAX_RETRIES
    assert settings.pipeline.retry_backoff_seconds == DEFAULT_PIPELINE_RETRY_BACKOFF_SECONDS
    assert settings.pipeline.stage_chunk_size == DEFAULT_PIPELINE_STAGE_CHUNK_SIZE
    assert settings.pipeline.promote_chunk_size == DEFAULT_PIPELINE_PROMOTE_CHUNK_SIZE
    assert settings.pipeline.max_concurrent_sources == DEFAULT_PIPELINE_MAX_CONCURRENT_SOURCES
    assert settings.pipeline.resume_enabled is DEFAULT_PIPELINE_RESUME_ENABLED
    assert settings.school_search.postcodes_io_base_url == DEFAULT_POSTCODES_IO_BASE_URL
    assert settings.school_search.postcode_cache_ttl_days == DEFAULT_POSTCODE_CACHE_TTL_DAYS
    assert (
        settings.data_quality.freshness_sla_hours_gias == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_dfe_characteristics
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_ofsted_latest
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_ofsted_timeline
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_ons_imd
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_police_crime_context
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.coverage_drift_threshold
        == DEFAULT_DATA_QUALITY_COVERAGE_DRIFT_THRESHOLD
    )
    assert (
        settings.data_quality.max_consecutive_hard_failures
        == DEFAULT_DATA_QUALITY_MAX_CONSECUTIVE_HARD_FAILURES
    )
    assert (
        settings.data_quality.sparse_trend_ratio_threshold
        == DEFAULT_DATA_QUALITY_SPARSE_TREND_RATIO_THRESHOLD
    )


def test_app_settings_reads_environment_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(
        "CIVITAS_DATABASE_URL", "postgresql+psycopg://override:override@localhost:5432/app"
    )
    monkeypatch.setenv("CIVITAS_BRONZE_ROOT", str(tmp_path / "custom-bronze"))
    monkeypatch.setenv("CIVITAS_GIAS_SOURCE_CSV", "  https://example.com/gias.csv  ")
    monkeypatch.setenv("CIVITAS_DEMOGRAPHICS_SOURCE_MODE", " release_files ")
    monkeypatch.setenv(
        "CIVITAS_DEMOGRAPHICS_SPC_PUBLICATION_SLUG",
        " school-pupils-and-their-characteristics ",
    )
    monkeypatch.setenv(
        "CIVITAS_DEMOGRAPHICS_SEN_PUBLICATION_SLUG",
        " special-educational-needs-in-england ",
    )
    monkeypatch.setenv(
        "CIVITAS_DEMOGRAPHICS_RELEASE_SLUGS",
        " 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25 ",
    )
    monkeypatch.setenv("CIVITAS_DEMOGRAPHICS_LOOKBACK_YEARS", "5")
    monkeypatch.setenv("CIVITAS_DEMOGRAPHICS_SOURCE_STRICT_MODE", "false")
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

    settings = AppSettings(_env_file=None)

    assert settings.database.url == "postgresql+psycopg://override:override@localhost:5432/app"
    assert settings.pipeline.bronze_root == tmp_path / "custom-bronze"
    assert settings.pipeline.gias_source_csv == "https://example.com/gias.csv"
    assert settings.pipeline.demographics_source_mode == "release_files"
    assert (
        settings.pipeline.demographics_spc_publication_slug
        == "school-pupils-and-their-characteristics"
    )
    assert (
        settings.pipeline.demographics_sen_publication_slug
        == "special-educational-needs-in-england"
    )
    assert settings.pipeline.demographics_release_slugs == (
        "2019-20",
        "2020-21",
        "2021-22",
        "2022-23",
        "2023-24",
        "2024-25",
    )
    assert settings.pipeline.demographics_lookback_years == 5
    assert settings.pipeline.demographics_source_strict_mode is False
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


def test_app_settings_validation_errors_on_invalid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIVITAS_DATABASE_URL", "")
    monkeypatch.setenv("CIVITAS_DEMOGRAPHICS_SOURCE_MODE", "legacy")
    monkeypatch.setenv("CIVITAS_DEMOGRAPHICS_LOOKBACK_YEARS", "0")
    monkeypatch.setenv("CIVITAS_IMD_RELEASE", "not-a-release")
    monkeypatch.setenv("CIVITAS_POLICE_CRIME_SOURCE_MODE", "invalid")
    monkeypatch.setenv("CIVITAS_POLICE_CRIME_RADIUS_METERS", "0")
    monkeypatch.setenv("CIVITAS_OFSTED_TIMELINE_YEARS", "0")
    monkeypatch.setenv("CIVITAS_PIPELINE_MAX_REJECT_RATIO_GIAS", "1.5")
    monkeypatch.setenv("CIVITAS_PIPELINE_MAX_RETRIES", "-1")
    monkeypatch.setenv("CIVITAS_PIPELINE_STAGE_CHUNK_SIZE", "0")
    monkeypatch.setenv("CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_GIAS", "0")
    monkeypatch.setenv("CIVITAS_DATA_QUALITY_COVERAGE_DRIFT_THRESHOLD", "1.2")
    monkeypatch.setenv("CIVITAS_DATA_QUALITY_MAX_CONSECUTIVE_HARD_FAILURES", "0")
    monkeypatch.setenv("CIVITAS_DATA_QUALITY_SPARSE_TREND_RATIO_THRESHOLD", "-0.1")

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
