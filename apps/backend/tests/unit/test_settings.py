from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from civitas.infrastructure.config.settings import (
    DEFAULT_AI_BATCH_SIZE,
    DEFAULT_AI_ENABLED,
    DEFAULT_AI_MAX_RETRIES,
    DEFAULT_AI_MODEL_ID,
    DEFAULT_AI_PROVIDER,
    DEFAULT_AI_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_AI_RETRY_BACKOFF_SECONDS,
    DEFAULT_ALLOW_NONCANONICAL_BRONZE_ROOT,
    DEFAULT_BILLING_ENABLED,
    DEFAULT_BILLING_PROVIDER,
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
    DEFAULT_DFE_ATTENDANCE_LOOKBACK_YEARS,
    DEFAULT_DFE_ATTENDANCE_PUBLICATION_SLUG,
    DEFAULT_DFE_ATTENDANCE_RELEASE_SLUGS,
    DEFAULT_DFE_BEHAVIOUR_LOOKBACK_YEARS,
    DEFAULT_DFE_BEHAVIOUR_PUBLICATION_SLUG,
    DEFAULT_DFE_BEHAVIOUR_RELEASE_SLUGS,
    DEFAULT_DFE_PERFORMANCE_KS2_DATASET_ID,
    DEFAULT_DFE_PERFORMANCE_KS4_DATASET_ID,
    DEFAULT_DFE_PERFORMANCE_LOOKBACK_YEARS,
    DEFAULT_DFE_PERFORMANCE_PAGE_SIZE,
    DEFAULT_DFE_WORKFORCE_LOOKBACK_YEARS,
    DEFAULT_DFE_WORKFORCE_PUBLICATION_SLUG,
    DEFAULT_DFE_WORKFORCE_RELEASE_SLUGS,
    DEFAULT_IMD_RELEASE,
    DEFAULT_KS4_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL,
    DEFAULT_KS4_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL,
    DEFAULT_KS4_SUBJECT_PERFORMANCE_SOURCE_URL,
    DEFAULT_LEAVER_DESTINATIONS_16_TO_18_DATA_CATALOGUE_URL,
    DEFAULT_LEAVER_DESTINATIONS_16_TO_18_RELEASE_PAGE_URL,
    DEFAULT_LEAVER_DESTINATIONS_16_TO_18_SOURCE_URL,
    DEFAULT_LEAVER_DESTINATIONS_KS4_DATA_CATALOGUE_URL,
    DEFAULT_LEAVER_DESTINATIONS_KS4_RELEASE_PAGE_URL,
    DEFAULT_LEAVER_DESTINATIONS_KS4_SOURCE_URL,
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
    DEFAULT_SCHOOL_ADMISSIONS_SOURCE_URL,
    DEFAULT_SCHOOL_FINANCIAL_BENCHMARKS_WORKBOOK_URLS,
    DEFAULT_SCHOOL_PROFILE_CACHE_INVALIDATION_POLL_SECONDS,
    DEFAULT_SCHOOL_PROFILE_CACHE_TTL_SECONDS,
    DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL,
    DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL,
    DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_SOURCE_URL,
    REPO_ENV_FILE,
    AppSettings,
    get_settings,
)

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "civitas"
SETTINGS_MODULE_PATH = SRC_ROOT / "infrastructure" / "config" / "settings.py"
ENV_ACCESS_PATTERN = re.compile(r"\bos\.(?:environ|getenv)\b|\benviron\s*\[")


def test_app_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "CIVITAS_DATABASE_URL",
        "CIVITAS_TEST_DATABASE_URL",
        "CIVITAS_BRONZE_ROOT",
        "CIVITAS_ALLOW_NONCANONICAL_BRONZE_ROOT",
        "CIVITAS_GIAS_SOURCE_CSV",
        "CIVITAS_GIAS_SOURCE_ZIP",
        "CIVITAS_DEMOGRAPHICS_SOURCE_MODE",
        "CIVITAS_DEMOGRAPHICS_SPC_PUBLICATION_SLUG",
        "CIVITAS_DEMOGRAPHICS_SEN_PUBLICATION_SLUG",
        "CIVITAS_DEMOGRAPHICS_RELEASE_SLUGS",
        "CIVITAS_DEMOGRAPHICS_LOOKBACK_YEARS",
        "CIVITAS_DEMOGRAPHICS_SOURCE_STRICT_MODE",
        "CIVITAS_DFE_ATTENDANCE_PUBLICATION_SLUG",
        "CIVITAS_DFE_ATTENDANCE_RELEASE_SLUGS",
        "CIVITAS_DFE_ATTENDANCE_LOOKBACK_YEARS",
        "CIVITAS_DFE_ATTENDANCE_SOURCE_STRICT_MODE",
        "CIVITAS_DFE_BEHAVIOUR_PUBLICATION_SLUG",
        "CIVITAS_DFE_BEHAVIOUR_RELEASE_SLUGS",
        "CIVITAS_DFE_BEHAVIOUR_LOOKBACK_YEARS",
        "CIVITAS_DFE_BEHAVIOUR_SOURCE_STRICT_MODE",
        "CIVITAS_DFE_WORKFORCE_PUBLICATION_SLUG",
        "CIVITAS_DFE_WORKFORCE_RELEASE_SLUGS",
        "CIVITAS_DFE_WORKFORCE_LOOKBACK_YEARS",
        "CIVITAS_DFE_WORKFORCE_SOURCE_STRICT_MODE",
        "CIVITAS_DFE_PERFORMANCE_KS2_DATASET_ID",
        "CIVITAS_DFE_PERFORMANCE_KS4_DATASET_ID",
        "CIVITAS_DFE_PERFORMANCE_LOOKBACK_YEARS",
        "CIVITAS_DFE_PERFORMANCE_PAGE_SIZE",
        "CIVITAS_SCHOOL_ADMISSIONS_SOURCE_CSV",
        "CIVITAS_SCHOOL_ADMISSIONS_SOURCE_URL",
        "CIVITAS_LEAVER_DESTINATIONS_KS4_SOURCE_CSV",
        "CIVITAS_LEAVER_DESTINATIONS_KS4_SOURCE_URL",
        "CIVITAS_LEAVER_DESTINATIONS_KS4_RELEASE_PAGE_URL",
        "CIVITAS_LEAVER_DESTINATIONS_KS4_DATA_CATALOGUE_URL",
        "CIVITAS_LEAVER_DESTINATIONS_16_TO_18_SOURCE_CSV",
        "CIVITAS_LEAVER_DESTINATIONS_16_TO_18_SOURCE_URL",
        "CIVITAS_LEAVER_DESTINATIONS_16_TO_18_RELEASE_PAGE_URL",
        "CIVITAS_LEAVER_DESTINATIONS_16_TO_18_DATA_CATALOGUE_URL",
        "CIVITAS_KS4_SUBJECT_PERFORMANCE_SOURCE_CSV",
        "CIVITAS_KS4_SUBJECT_PERFORMANCE_SOURCE_URL",
        "CIVITAS_KS4_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL",
        "CIVITAS_KS4_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL",
        "CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_SOURCE_CSV",
        "CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_SOURCE_URL",
        "CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL",
        "CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL",
        "CIVITAS_SCHOOL_FINANCIAL_BENCHMARKS_WORKBOOK_URLS",
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
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_ATTENDANCE",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_BEHAVIOUR",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_WORKFORCE",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_PERFORMANCE",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_SCHOOL_ADMISSIONS",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_LEAVER_DESTINATIONS",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_KS4_SUBJECT_PERFORMANCE",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE",
        "CIVITAS_PIPELINE_MAX_REJECT_RATIO_SCHOOL_FINANCIAL_BENCHMARKS",
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
        "CIVITAS_SCHOOL_PROFILE_CACHE_TTL_SECONDS",
        "CIVITAS_SCHOOL_PROFILE_CACHE_INVALIDATION_POLL_SECONDS",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_GIAS",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_CHARACTERISTICS",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_ATTENDANCE",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_BEHAVIOUR",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_WORKFORCE",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_PERFORMANCE",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_SCHOOL_ADMISSIONS",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_LEAVER_DESTINATIONS",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_KS4_SUBJECT_PERFORMANCE",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_SCHOOL_FINANCIAL_BENCHMARKS",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_OFSTED_LATEST",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_OFSTED_TIMELINE",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_ONS_IMD",
        "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_POLICE_CRIME_CONTEXT",
        "CIVITAS_DATA_QUALITY_COVERAGE_DRIFT_THRESHOLD",
        "CIVITAS_DATA_QUALITY_MAX_CONSECUTIVE_HARD_FAILURES",
        "CIVITAS_DATA_QUALITY_SPARSE_TREND_RATIO_THRESHOLD",
        "CIVITAS_AI_ENABLED",
        "CIVITAS_AI_PROVIDER",
        "CIVITAS_AI_MODEL_ID",
        "CIVITAS_AI_API_KEY",
        "CIVITAS_AI_API_BASE_URL",
        "CIVITAS_AI_BATCH_SIZE",
        "CIVITAS_AI_REQUEST_TIMEOUT_SECONDS",
        "CIVITAS_AI_MAX_RETRIES",
        "CIVITAS_AI_RETRY_BACKOFF_SECONDS",
        "CIVITAS_RUNTIME_ENVIRONMENT",
        "CIVITAS_AUTH_PROVIDER",
        "CIVITAS_AUTH_SESSION_COOKIE_NAME",
        "CIVITAS_AUTH_SESSION_COOKIE_SECURE",
        "CIVITAS_AUTH_SESSION_COOKIE_SAMESITE",
        "CIVITAS_AUTH_SESSION_TTL_HOURS",
        "CIVITAS_AUTH_STATE_TTL_MINUTES",
        "CIVITAS_AUTH_CALLBACK_ERROR_PATH",
        "CIVITAS_AUTH_ALLOWED_ORIGINS",
        "CIVITAS_AUTH_SHARED_SECRET",
        "CIVITAS_AUTH_AUTH0_DOMAIN",
        "CIVITAS_AUTH_AUTH0_CLIENT_ID",
        "CIVITAS_AUTH_AUTH0_CLIENT_SECRET",
        "CIVITAS_AUTH_AUTH0_AUDIENCE",
        "CIVITAS_AUTH_AUTH0_CONNECTION",
        "CIVITAS_BILLING_ENABLED",
        "CIVITAS_BILLING_PROVIDER",
        "CIVITAS_BILLING_STRIPE_SECRET_KEY",
        "CIVITAS_BILLING_STRIPE_WEBHOOK_SECRET",
        "CIVITAS_BILLING_STRIPE_PORTAL_CONFIGURATION_ID",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = AppSettings(_env_file=None)

    assert settings.database.url == DEFAULT_DATABASE_URL
    assert settings.allow_noncanonical_bronze_root is DEFAULT_ALLOW_NONCANONICAL_BRONZE_ROOT
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
    assert (
        settings.pipeline.dfe_attendance_publication_slug == DEFAULT_DFE_ATTENDANCE_PUBLICATION_SLUG
    )
    assert settings.pipeline.dfe_attendance_release_slugs == DEFAULT_DFE_ATTENDANCE_RELEASE_SLUGS
    assert settings.pipeline.dfe_attendance_lookback_years == DEFAULT_DFE_ATTENDANCE_LOOKBACK_YEARS
    assert settings.pipeline.dfe_attendance_source_strict_mode is True
    assert (
        settings.pipeline.dfe_behaviour_publication_slug == DEFAULT_DFE_BEHAVIOUR_PUBLICATION_SLUG
    )
    assert settings.pipeline.dfe_behaviour_release_slugs == DEFAULT_DFE_BEHAVIOUR_RELEASE_SLUGS
    assert settings.pipeline.dfe_behaviour_lookback_years == DEFAULT_DFE_BEHAVIOUR_LOOKBACK_YEARS
    assert settings.pipeline.dfe_behaviour_source_strict_mode is True
    assert (
        settings.pipeline.dfe_workforce_publication_slug == DEFAULT_DFE_WORKFORCE_PUBLICATION_SLUG
    )
    assert settings.pipeline.dfe_workforce_release_slugs == DEFAULT_DFE_WORKFORCE_RELEASE_SLUGS
    assert settings.pipeline.dfe_workforce_lookback_years == DEFAULT_DFE_WORKFORCE_LOOKBACK_YEARS
    assert settings.pipeline.dfe_workforce_source_strict_mode is True
    assert (
        settings.pipeline.dfe_performance_ks2_dataset_id == DEFAULT_DFE_PERFORMANCE_KS2_DATASET_ID
    )
    assert (
        settings.pipeline.dfe_performance_ks4_dataset_id == DEFAULT_DFE_PERFORMANCE_KS4_DATASET_ID
    )
    assert (
        settings.pipeline.dfe_performance_lookback_years == DEFAULT_DFE_PERFORMANCE_LOOKBACK_YEARS
    )
    assert settings.pipeline.dfe_performance_page_size == DEFAULT_DFE_PERFORMANCE_PAGE_SIZE
    assert settings.pipeline.school_admissions_source_csv is None
    assert settings.pipeline.school_admissions_source_url == DEFAULT_SCHOOL_ADMISSIONS_SOURCE_URL
    assert settings.pipeline.leaver_destinations_ks4_source_csv is None
    assert (
        settings.pipeline.leaver_destinations_ks4_source_url
        == DEFAULT_LEAVER_DESTINATIONS_KS4_SOURCE_URL
    )
    assert (
        settings.pipeline.leaver_destinations_ks4_release_page_url
        == DEFAULT_LEAVER_DESTINATIONS_KS4_RELEASE_PAGE_URL
    )
    assert (
        settings.pipeline.leaver_destinations_ks4_data_catalogue_url
        == DEFAULT_LEAVER_DESTINATIONS_KS4_DATA_CATALOGUE_URL
    )
    assert settings.pipeline.leaver_destinations_16_to_18_source_csv is None
    assert (
        settings.pipeline.leaver_destinations_16_to_18_source_url
        == DEFAULT_LEAVER_DESTINATIONS_16_TO_18_SOURCE_URL
    )
    assert (
        settings.pipeline.leaver_destinations_16_to_18_release_page_url
        == DEFAULT_LEAVER_DESTINATIONS_16_TO_18_RELEASE_PAGE_URL
    )
    assert (
        settings.pipeline.leaver_destinations_16_to_18_data_catalogue_url
        == DEFAULT_LEAVER_DESTINATIONS_16_TO_18_DATA_CATALOGUE_URL
    )
    assert settings.pipeline.ks4_subject_performance_source_csv is None
    assert (
        settings.pipeline.ks4_subject_performance_source_url
        == DEFAULT_KS4_SUBJECT_PERFORMANCE_SOURCE_URL
    )
    assert (
        settings.pipeline.ks4_subject_performance_release_page_url
        == DEFAULT_KS4_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL
    )
    assert (
        settings.pipeline.ks4_subject_performance_data_catalogue_url
        == DEFAULT_KS4_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL
    )
    assert settings.pipeline.sixteen_to_eighteen_subject_performance_source_csv is None
    assert (
        settings.pipeline.sixteen_to_eighteen_subject_performance_source_url
        == DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_SOURCE_URL
    )
    assert (
        settings.pipeline.sixteen_to_eighteen_subject_performance_release_page_url
        == DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL
    )
    assert (
        settings.pipeline.sixteen_to_eighteen_subject_performance_data_catalogue_url
        == DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL
    )
    assert (
        settings.pipeline.school_financial_benchmarks_workbook_urls
        == DEFAULT_SCHOOL_FINANCIAL_BENCHMARKS_WORKBOOK_URLS
    )
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
    assert settings.pipeline.max_reject_ratio_dfe_attendance == 1.0
    assert settings.pipeline.max_reject_ratio_dfe_behaviour == 1.0
    assert settings.pipeline.max_reject_ratio_dfe_workforce == 1.0
    assert settings.pipeline.max_reject_ratio_dfe_performance == 1.0
    assert settings.pipeline.max_reject_ratio_school_admissions == 1.0
    assert settings.pipeline.max_reject_ratio_leaver_destinations == 1.0
    assert settings.pipeline.max_reject_ratio_ks4_subject_performance == 1.0
    assert settings.pipeline.max_reject_ratio_sixteen_to_eighteen_subject_performance == 1.0
    assert settings.pipeline.max_reject_ratio_school_financial_benchmarks == 1.0
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
        settings.school_search.profile_cache_ttl_seconds == DEFAULT_SCHOOL_PROFILE_CACHE_TTL_SECONDS
    )
    assert (
        settings.school_search.profile_cache_invalidation_poll_seconds
        == DEFAULT_SCHOOL_PROFILE_CACHE_INVALIDATION_POLL_SECONDS
    )
    assert (
        settings.data_quality.freshness_sla_hours_gias == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_dfe_characteristics
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_dfe_attendance
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_dfe_behaviour
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_dfe_workforce
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_dfe_performance
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_school_admissions
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_leaver_destinations
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_ks4_subject_performance
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_sixteen_to_eighteen_subject_performance
        == DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS
    )
    assert (
        settings.data_quality.freshness_sla_hours_school_financial_benchmarks
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
    assert settings.ai.enabled is DEFAULT_AI_ENABLED
    assert settings.ai.provider == DEFAULT_AI_PROVIDER
    assert settings.ai.model_id == DEFAULT_AI_MODEL_ID
    assert settings.ai.api_key == ""
    assert settings.ai.api_base_url == ""
    assert settings.ai.batch_size == DEFAULT_AI_BATCH_SIZE
    assert settings.ai.request_timeout_seconds == DEFAULT_AI_REQUEST_TIMEOUT_SECONDS
    assert settings.ai.max_retries == DEFAULT_AI_MAX_RETRIES
    assert settings.ai.retry_backoff_seconds == DEFAULT_AI_RETRY_BACKOFF_SECONDS
    assert settings.billing.enabled is DEFAULT_BILLING_ENABLED
    assert settings.billing.provider == DEFAULT_BILLING_PROVIDER
    assert settings.billing.stripe is None


def test_app_settings_reads_environment_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(
        "CIVITAS_DATABASE_URL", "postgresql+psycopg://override:override@localhost:5432/app"
    )
    monkeypatch.setenv(
        "CIVITAS_TEST_DATABASE_URL",
        "postgresql+psycopg://override:override@localhost:5432/app_test",
    )
    monkeypatch.setenv("CIVITAS_BRONZE_ROOT", str(tmp_path / "custom-bronze"))
    monkeypatch.setenv("CIVITAS_ALLOW_NONCANONICAL_BRONZE_ROOT", "true")
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
    monkeypatch.setenv(
        "CIVITAS_DFE_ATTENDANCE_PUBLICATION_SLUG",
        " pupil-absence-in-schools-in-england ",
    )
    monkeypatch.setenv("CIVITAS_DFE_ATTENDANCE_RELEASE_SLUGS", " 2021-22, 2022-23, 2023-24 ")
    monkeypatch.setenv("CIVITAS_DFE_ATTENDANCE_LOOKBACK_YEARS", "2")
    monkeypatch.setenv("CIVITAS_DFE_ATTENDANCE_SOURCE_STRICT_MODE", "false")
    monkeypatch.setenv(
        "CIVITAS_DFE_BEHAVIOUR_PUBLICATION_SLUG",
        " suspensions-and-permanent-exclusions-in-england ",
    )
    monkeypatch.setenv(
        "CIVITAS_DFE_BEHAVIOUR_RELEASE_SLUGS",
        " 2022-23, 2023-24, 2024-25-autumn-term ",
    )
    monkeypatch.setenv("CIVITAS_DFE_BEHAVIOUR_LOOKBACK_YEARS", "2")
    monkeypatch.setenv("CIVITAS_DFE_BEHAVIOUR_SOURCE_STRICT_MODE", "false")
    monkeypatch.setenv(
        "CIVITAS_DFE_WORKFORCE_PUBLICATION_SLUG",
        " school-workforce-in-england ",
    )
    monkeypatch.setenv("CIVITAS_DFE_WORKFORCE_RELEASE_SLUGS", " 2022, 2023, 2024 ")
    monkeypatch.setenv("CIVITAS_DFE_WORKFORCE_LOOKBACK_YEARS", "2")
    monkeypatch.setenv("CIVITAS_DFE_WORKFORCE_SOURCE_STRICT_MODE", "false")
    monkeypatch.setenv(
        "CIVITAS_DFE_PERFORMANCE_KS2_DATASET_ID",
        " 019afee4-e5d0-72f9-9a8f-d7a1a56eac1d ",
    )
    monkeypatch.setenv(
        "CIVITAS_DFE_PERFORMANCE_KS4_DATASET_ID",
        " 19e39901-a96c-be76-b9c2-6af54ae076d2 ",
    )
    monkeypatch.setenv("CIVITAS_DFE_PERFORMANCE_LOOKBACK_YEARS", "4")
    monkeypatch.setenv("CIVITAS_DFE_PERFORMANCE_PAGE_SIZE", "5000")
    monkeypatch.setenv(
        "CIVITAS_SCHOOL_ADMISSIONS_SOURCE_CSV",
        "  https://example.com/school_admissions.csv  ",
    )
    monkeypatch.setenv(
        "CIVITAS_SCHOOL_ADMISSIONS_SOURCE_URL",
        "  https://content.example.test/release/file  ",
    )
    monkeypatch.setenv(
        "CIVITAS_LEAVER_DESTINATIONS_KS4_SOURCE_CSV",
        "  https://example.com/ks4.csv  ",
    )
    monkeypatch.setenv(
        "CIVITAS_LEAVER_DESTINATIONS_KS4_SOURCE_URL",
        "  https://content.example.test/ks4  ",
    )
    monkeypatch.setenv(
        "CIVITAS_LEAVER_DESTINATIONS_KS4_RELEASE_PAGE_URL",
        "  https://example.com/ks4-release  ",
    )
    monkeypatch.setenv(
        "CIVITAS_LEAVER_DESTINATIONS_KS4_DATA_CATALOGUE_URL",
        "  https://example.com/ks4-catalogue  ",
    )
    monkeypatch.setenv(
        "CIVITAS_LEAVER_DESTINATIONS_16_TO_18_SOURCE_CSV",
        "  https://example.com/16-to-18.csv  ",
    )
    monkeypatch.setenv(
        "CIVITAS_LEAVER_DESTINATIONS_16_TO_18_SOURCE_URL",
        "  https://content.example.test/16-to-18  ",
    )
    monkeypatch.setenv(
        "CIVITAS_LEAVER_DESTINATIONS_16_TO_18_RELEASE_PAGE_URL",
        "  https://example.com/16-to-18-release  ",
    )
    monkeypatch.setenv(
        "CIVITAS_LEAVER_DESTINATIONS_16_TO_18_DATA_CATALOGUE_URL",
        "  https://example.com/16-to-18-catalogue  ",
    )
    monkeypatch.setenv(
        "CIVITAS_KS4_SUBJECT_PERFORMANCE_SOURCE_CSV",
        "  https://example.com/ks4-subject-performance.csv  ",
    )
    monkeypatch.setenv(
        "CIVITAS_KS4_SUBJECT_PERFORMANCE_SOURCE_URL",
        "  https://content.example.test/ks4-subject-performance  ",
    )
    monkeypatch.setenv(
        "CIVITAS_KS4_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL",
        "  https://example.com/ks4-subject-performance-release  ",
    )
    monkeypatch.setenv(
        "CIVITAS_KS4_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL",
        "  https://example.com/ks4-subject-performance-catalogue  ",
    )
    monkeypatch.setenv(
        "CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_SOURCE_CSV",
        "  https://example.com/16-to-18-subject-performance.csv  ",
    )
    monkeypatch.setenv(
        "CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_SOURCE_URL",
        "  https://content.example.test/16-to-18-subject-performance  ",
    )
    monkeypatch.setenv(
        "CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL",
        "  https://example.com/16-to-18-subject-performance-release  ",
    )
    monkeypatch.setenv(
        "CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL",
        "  https://example.com/16-to-18-subject-performance-catalogue  ",
    )
    monkeypatch.setenv(
        "CIVITAS_SCHOOL_FINANCIAL_BENCHMARKS_WORKBOOK_URLS",
        " https://example.com/AAR_2022-23_download.xlsx, https://example.com/AAR_2023-24_download.xlsx ",
    )
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
    monkeypatch.setenv("CIVITAS_POSTCODES_IO_BASE_URL", "https://api.example.test")
    monkeypatch.setenv("CIVITAS_POSTCODE_CACHE_TTL_DAYS", "45")
    monkeypatch.setenv("CIVITAS_SCHOOL_PROFILE_CACHE_TTL_SECONDS", "120")
    monkeypatch.setenv("CIVITAS_SCHOOL_PROFILE_CACHE_INVALIDATION_POLL_SECONDS", "3")
    monkeypatch.setenv("CIVITAS_AI_ENABLED", "true")
    monkeypatch.setenv("CIVITAS_AI_PROVIDER", " openai_compatible ")
    monkeypatch.setenv("CIVITAS_AI_MODEL_ID", " local-model ")
    monkeypatch.setenv("CIVITAS_AI_API_KEY", " test-key ")
    monkeypatch.setenv("CIVITAS_AI_API_BASE_URL", " https://llm.example.test/v1 ")
    monkeypatch.setenv("CIVITAS_AI_BATCH_SIZE", "25")
    monkeypatch.setenv("CIVITAS_AI_REQUEST_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("CIVITAS_AI_MAX_RETRIES", "3")
    monkeypatch.setenv("CIVITAS_AI_RETRY_BACKOFF_SECONDS", "0.75")
    monkeypatch.setenv("CIVITAS_BILLING_ENABLED", "true")
    monkeypatch.setenv("CIVITAS_BILLING_PROVIDER", " stripe ")
    monkeypatch.setenv("CIVITAS_BILLING_STRIPE_SECRET_KEY", " sk_test_123 ")
    monkeypatch.setenv("CIVITAS_BILLING_STRIPE_WEBHOOK_SECRET", " whsec_test_123 ")
    monkeypatch.setenv(
        "CIVITAS_BILLING_STRIPE_PORTAL_CONFIGURATION_ID",
        " bpc_test_123 ",
    )

    settings = AppSettings(_env_file=None)

    assert settings.database.url == "postgresql+psycopg://override:override@localhost:5432/app"
    assert (
        settings.test_database_url
        == "postgresql+psycopg://override:override@localhost:5432/app_test"
    )
    assert settings.allow_noncanonical_bronze_root is True
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
    assert (
        settings.pipeline.dfe_attendance_publication_slug == "pupil-absence-in-schools-in-england"
    )
    assert settings.pipeline.dfe_attendance_release_slugs == ("2021-22", "2022-23", "2023-24")
    assert settings.pipeline.dfe_attendance_lookback_years == 2
    assert settings.pipeline.dfe_attendance_source_strict_mode is False
    assert (
        settings.pipeline.dfe_behaviour_publication_slug
        == "suspensions-and-permanent-exclusions-in-england"
    )
    assert settings.pipeline.dfe_behaviour_release_slugs == (
        "2022-23",
        "2023-24",
        "2024-25-autumn-term",
    )
    assert settings.pipeline.dfe_behaviour_lookback_years == 2
    assert settings.pipeline.dfe_behaviour_source_strict_mode is False
    assert settings.pipeline.dfe_workforce_publication_slug == "school-workforce-in-england"
    assert settings.pipeline.dfe_workforce_release_slugs == ("2022", "2023", "2024")
    assert settings.pipeline.dfe_workforce_lookback_years == 2
    assert settings.pipeline.dfe_workforce_source_strict_mode is False
    assert (
        settings.pipeline.dfe_performance_ks2_dataset_id == "019afee4-e5d0-72f9-9a8f-d7a1a56eac1d"
    )
    assert (
        settings.pipeline.dfe_performance_ks4_dataset_id == "19e39901-a96c-be76-b9c2-6af54ae076d2"
    )
    assert settings.pipeline.dfe_performance_lookback_years == 4
    assert settings.pipeline.dfe_performance_page_size == 5000
    assert (
        settings.pipeline.school_admissions_source_csv
        == "https://example.com/school_admissions.csv"
    )
    assert (
        settings.pipeline.school_admissions_source_url
        == "https://content.example.test/release/file"
    )
    assert settings.pipeline.leaver_destinations_ks4_source_csv == "https://example.com/ks4.csv"
    assert (
        settings.pipeline.leaver_destinations_ks4_source_url == "https://content.example.test/ks4"
    )
    assert (
        settings.pipeline.leaver_destinations_ks4_release_page_url
        == "https://example.com/ks4-release"
    )
    assert (
        settings.pipeline.leaver_destinations_ks4_data_catalogue_url
        == "https://example.com/ks4-catalogue"
    )
    assert (
        settings.pipeline.leaver_destinations_16_to_18_source_csv
        == "https://example.com/16-to-18.csv"
    )
    assert (
        settings.pipeline.leaver_destinations_16_to_18_source_url
        == "https://content.example.test/16-to-18"
    )
    assert (
        settings.pipeline.leaver_destinations_16_to_18_release_page_url
        == "https://example.com/16-to-18-release"
    )
    assert (
        settings.pipeline.leaver_destinations_16_to_18_data_catalogue_url
        == "https://example.com/16-to-18-catalogue"
    )
    assert (
        settings.pipeline.ks4_subject_performance_source_csv
        == "https://example.com/ks4-subject-performance.csv"
    )
    assert (
        settings.pipeline.ks4_subject_performance_source_url
        == "https://content.example.test/ks4-subject-performance"
    )
    assert (
        settings.pipeline.ks4_subject_performance_release_page_url
        == "https://example.com/ks4-subject-performance-release"
    )
    assert (
        settings.pipeline.ks4_subject_performance_data_catalogue_url
        == "https://example.com/ks4-subject-performance-catalogue"
    )
    assert (
        settings.pipeline.sixteen_to_eighteen_subject_performance_source_csv
        == "https://example.com/16-to-18-subject-performance.csv"
    )
    assert (
        settings.pipeline.sixteen_to_eighteen_subject_performance_source_url
        == "https://content.example.test/16-to-18-subject-performance"
    )
    assert (
        settings.pipeline.sixteen_to_eighteen_subject_performance_release_page_url
        == "https://example.com/16-to-18-subject-performance-release"
    )
    assert (
        settings.pipeline.sixteen_to_eighteen_subject_performance_data_catalogue_url
        == "https://example.com/16-to-18-subject-performance-catalogue"
    )
    assert settings.pipeline.school_financial_benchmarks_workbook_urls == (
        "https://example.com/AAR_2022-23_download.xlsx",
        "https://example.com/AAR_2023-24_download.xlsx",
    )
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
    assert settings.school_search.postcodes_io_base_url == "https://api.example.test"
    assert settings.school_search.postcode_cache_ttl_days == 45
    assert settings.school_search.profile_cache_ttl_seconds == 120
    assert settings.school_search.profile_cache_invalidation_poll_seconds == 3.0
    assert settings.ai.enabled is True
    assert settings.ai.provider == "openai_compatible"
    assert settings.ai.model_id == "local-model"
    assert settings.ai.api_key == "test-key"
    assert settings.ai.api_base_url == "https://llm.example.test/v1"
    assert settings.ai.batch_size == 25
    assert settings.ai.request_timeout_seconds == 45.0
    assert settings.ai.max_retries == 3
    assert settings.ai.retry_backoff_seconds == 0.75
    assert settings.billing.enabled is True
    assert settings.billing.provider == "stripe"
    assert settings.billing.stripe is not None
    assert settings.billing.stripe.secret_key == "sk_test_123"
    assert settings.billing.stripe.webhook_secret == "whsec_test_123"
    assert settings.billing.stripe.portal_configuration_id == "bpc_test_123"


def test_app_settings_rejects_noncanonical_bronze_root_without_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CIVITAS_BRONZE_ROOT", str(tmp_path / "custom-bronze"))

    with pytest.raises(
        ValidationError,
        match="CIVITAS_BRONZE_ROOT must remain at data/bronze",
    ):
        AppSettings(_env_file=None)


def test_app_settings_validation_errors_on_invalid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIVITAS_DATABASE_URL", "")
    monkeypatch.setenv("CIVITAS_DEMOGRAPHICS_SOURCE_MODE", "legacy")
    monkeypatch.setenv("CIVITAS_DEMOGRAPHICS_LOOKBACK_YEARS", "0")
    monkeypatch.setenv("CIVITAS_DFE_ATTENDANCE_LOOKBACK_YEARS", "0")
    monkeypatch.setenv("CIVITAS_DFE_BEHAVIOUR_LOOKBACK_YEARS", "0")
    monkeypatch.setenv("CIVITAS_DFE_WORKFORCE_LOOKBACK_YEARS", "0")
    monkeypatch.setenv("CIVITAS_DFE_PERFORMANCE_LOOKBACK_YEARS", "0")
    monkeypatch.setenv("CIVITAS_DFE_PERFORMANCE_PAGE_SIZE", "10001")
    monkeypatch.setenv("CIVITAS_IMD_RELEASE", "not-a-release")
    monkeypatch.setenv("CIVITAS_POLICE_CRIME_SOURCE_MODE", "invalid")
    monkeypatch.setenv("CIVITAS_POLICE_CRIME_RADIUS_METERS", "0")
    monkeypatch.setenv("CIVITAS_OFSTED_TIMELINE_YEARS", "0")
    monkeypatch.setenv("CIVITAS_PIPELINE_MAX_REJECT_RATIO_GIAS", "1.5")
    monkeypatch.setenv("CIVITAS_PIPELINE_MAX_RETRIES", "-1")
    monkeypatch.setenv("CIVITAS_PIPELINE_STAGE_CHUNK_SIZE", "0")
    monkeypatch.setenv("CIVITAS_SCHOOL_PROFILE_CACHE_TTL_SECONDS", "-1")
    monkeypatch.setenv("CIVITAS_SCHOOL_PROFILE_CACHE_INVALIDATION_POLL_SECONDS", "0")
    monkeypatch.setenv("CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_GIAS", "0")
    monkeypatch.setenv("CIVITAS_DATA_QUALITY_COVERAGE_DRIFT_THRESHOLD", "1.2")
    monkeypatch.setenv("CIVITAS_DATA_QUALITY_MAX_CONSECUTIVE_HARD_FAILURES", "0")
    monkeypatch.setenv("CIVITAS_DATA_QUALITY_SPARSE_TREND_RATIO_THRESHOLD", "-0.1")
    monkeypatch.setenv("CIVITAS_AI_ENABLED", "true")
    monkeypatch.setenv("CIVITAS_AI_PROVIDER", "unsupported")
    monkeypatch.setenv("CIVITAS_AI_BATCH_SIZE", "0")

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


def test_app_settings_requires_ai_key_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIVITAS_AI_ENABLED", "true")
    monkeypatch.delenv("CIVITAS_AI_API_KEY", raising=False)

    with pytest.raises(ValidationError, match="CIVITAS_AI_API_KEY"):
        AppSettings(_env_file=None)


def test_app_settings_requires_billing_secrets_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_BILLING_ENABLED", "true")
    monkeypatch.delenv("CIVITAS_BILLING_STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("CIVITAS_BILLING_STRIPE_WEBHOOK_SECRET", raising=False)

    with pytest.raises(
        ValidationError,
        match="CIVITAS_BILLING_STRIPE_SECRET_KEY and CIVITAS_BILLING_STRIPE_WEBHOOK_SECRET",
    ):
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


def test_settings_model_uses_repo_root_env_file() -> None:
    assert REPO_ENV_FILE.is_absolute()
    assert Path(__file__).resolve().parents[4] / ".env" == REPO_ENV_FILE
    assert AppSettings.model_config.get("env_file") == REPO_ENV_FILE
