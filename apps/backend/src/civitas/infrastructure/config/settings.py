from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import (
    BaseModel,
    Field,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+psycopg://app:app@localhost:5432/app"
DEFAULT_BRONZE_ROOT = Path("data/bronze")
DEFAULT_DEMOGRAPHICS_SOURCE_MODE = "release_files"
DEFAULT_DEMOGRAPHICS_SPC_PUBLICATION_SLUG = "school-pupils-and-their-characteristics"
DEFAULT_DEMOGRAPHICS_SEN_PUBLICATION_SLUG = "special-educational-needs-in-england"
DEFAULT_DEMOGRAPHICS_RELEASE_SLUGS = (
    "2019-20",
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
)
DEFAULT_DEMOGRAPHICS_LOOKBACK_YEARS = 6
DEFAULT_DEMOGRAPHICS_SOURCE_STRICT_MODE = True
DEFAULT_DFE_ATTENDANCE_PUBLICATION_SLUG = "pupil-absence-in-schools-in-england"
DEFAULT_DFE_ATTENDANCE_RELEASE_SLUGS = (
    "2021-22",
    "2022-23",
    "2023-24",
)
DEFAULT_DFE_ATTENDANCE_LOOKBACK_YEARS = 3
DEFAULT_DFE_ATTENDANCE_SOURCE_STRICT_MODE = True
DEFAULT_DFE_BEHAVIOUR_PUBLICATION_SLUG = "suspensions-and-permanent-exclusions-in-england"
DEFAULT_DFE_BEHAVIOUR_RELEASE_SLUGS = (
    "2022-23",
    "2023-24",
    "2024-25-autumn-term",
)
DEFAULT_DFE_BEHAVIOUR_LOOKBACK_YEARS = 3
DEFAULT_DFE_BEHAVIOUR_SOURCE_STRICT_MODE = True
DEFAULT_DFE_WORKFORCE_PUBLICATION_SLUG = "school-workforce-in-england"
DEFAULT_DFE_WORKFORCE_RELEASE_SLUGS = (
    "2022",
    "2023",
    "2024",
)
DEFAULT_DFE_WORKFORCE_LOOKBACK_YEARS = 3
DEFAULT_DFE_WORKFORCE_SOURCE_STRICT_MODE = True
DEFAULT_DFE_PERFORMANCE_KS2_DATASET_ID = "019afee4-e5d0-72f9-9a8f-d7a1a56eac1d"
DEFAULT_DFE_PERFORMANCE_KS4_DATASET_ID = "19e39901-a96c-be76-b9c2-6af54ae076d2"
DEFAULT_DFE_PERFORMANCE_LOOKBACK_YEARS = 3
DEFAULT_DFE_PERFORMANCE_PAGE_SIZE = 10_000
DEFAULT_IMD_RELEASE = "iod2025"
DEFAULT_HOUSE_PRICES_SOURCE_URL = (
    "https://publicdata.landregistry.gov.uk/market-trend-data/"
    "house-price-index-data/Average-prices-2025-12.csv"
)
DEFAULT_POLICE_CRIME_SOURCE_MODE = "archive"
DEFAULT_POLICE_CRIME_RADIUS_METERS = 1609.344
DEFAULT_OFSTED_TIMELINE_YEARS = 10
DEFAULT_PIPELINE_MAX_REJECT_RATIO = 1.0
DEFAULT_PIPELINE_HTTP_TIMEOUT_SECONDS = 60.0
DEFAULT_PIPELINE_MAX_RETRIES = 2
DEFAULT_PIPELINE_RETRY_BACKOFF_SECONDS = 0.5
DEFAULT_PIPELINE_STAGE_CHUNK_SIZE = 1000
DEFAULT_PIPELINE_PROMOTE_CHUNK_SIZE = 1000
DEFAULT_PIPELINE_MAX_CONCURRENT_SOURCES = 1
DEFAULT_PIPELINE_RESUME_ENABLED = True
DEFAULT_ALLOW_NONCANONICAL_BRONZE_ROOT = False
DEFAULT_OFSTED_TIMELINE_SOURCE_INDEX_URL = (
    "https://www.gov.uk/government/statistical-data-sets/"
    "monthly-management-information-ofsteds-school-inspections-outcomes"
)
DEFAULT_POSTCODES_IO_BASE_URL = "https://api.postcodes.io"
DEFAULT_POSTCODE_CACHE_TTL_DAYS = 30
DEFAULT_SCHOOL_PROFILE_CACHE_TTL_SECONDS = 300
DEFAULT_SCHOOL_PROFILE_CACHE_INVALIDATION_POLL_SECONDS = 2.0
DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS = 720
DEFAULT_DATA_QUALITY_COVERAGE_DRIFT_THRESHOLD = 0.05
DEFAULT_DATA_QUALITY_MAX_CONSECUTIVE_HARD_FAILURES = 2
DEFAULT_DATA_QUALITY_SPARSE_TREND_RATIO_THRESHOLD = 0.7
DEFAULT_AI_ENABLED = False
DEFAULT_AI_PROVIDER = "grok"
DEFAULT_AI_MODEL_ID = "grok-4-1-fast-reasoning"
DEFAULT_AI_API_BASE_URL: str | None = None
DEFAULT_AI_BATCH_SIZE = 10
DEFAULT_AI_REQUEST_TIMEOUT_SECONDS = 30.0
DEFAULT_AI_MAX_RETRIES = 2
DEFAULT_AI_RETRY_BACKOFF_SECONDS = 0.5


class DatabaseSettings(BaseModel):
    url: str


class PipelineSettings(BaseModel):
    bronze_root: Path
    gias_source_csv: str | None = None
    gias_source_zip: str | None = None
    demographics_source_mode: str
    demographics_spc_publication_slug: str
    demographics_sen_publication_slug: str
    demographics_release_slugs: tuple[str, ...]
    demographics_lookback_years: PositiveInt
    demographics_source_strict_mode: bool
    dfe_attendance_publication_slug: str
    dfe_attendance_release_slugs: tuple[str, ...]
    dfe_attendance_lookback_years: PositiveInt
    dfe_attendance_source_strict_mode: bool
    dfe_behaviour_publication_slug: str
    dfe_behaviour_release_slugs: tuple[str, ...]
    dfe_behaviour_lookback_years: PositiveInt
    dfe_behaviour_source_strict_mode: bool
    dfe_workforce_publication_slug: str
    dfe_workforce_release_slugs: tuple[str, ...]
    dfe_workforce_lookback_years: PositiveInt
    dfe_workforce_source_strict_mode: bool
    dfe_performance_ks2_dataset_id: str
    dfe_performance_ks4_dataset_id: str
    dfe_performance_lookback_years: PositiveInt
    dfe_performance_page_size: PositiveInt
    imd_source_csv: str | None = None
    imd_release: str
    house_prices_source_csv: str | None = None
    house_prices_source_url: str | None = None
    police_crime_source_archive_url: str | None = None
    police_crime_source_mode: str
    police_crime_radius_meters: PositiveFloat
    ofsted_latest_source_csv: str | None = None
    ofsted_timeline_source_index_url: str
    ofsted_timeline_source_assets: str | None = None
    ofsted_timeline_years: PositiveInt
    ofsted_timeline_include_historical_baseline: bool = True
    max_reject_ratio_gias: float
    max_reject_ratio_dfe_characteristics: float
    max_reject_ratio_dfe_attendance: float
    max_reject_ratio_dfe_behaviour: float
    max_reject_ratio_dfe_workforce: float
    max_reject_ratio_dfe_performance: float
    max_reject_ratio_ofsted_latest: float
    max_reject_ratio_ofsted_timeline: float
    max_reject_ratio_ons_imd: float
    max_reject_ratio_uk_house_prices: float
    max_reject_ratio_police_crime_context: float
    http_timeout_seconds: PositiveFloat
    max_retries: NonNegativeInt
    retry_backoff_seconds: PositiveFloat
    stage_chunk_size: PositiveInt
    promote_chunk_size: PositiveInt
    max_concurrent_sources: PositiveInt
    resume_enabled: bool


class HttpClientSettings(BaseModel):
    timeout_seconds: PositiveFloat
    max_retries: NonNegativeInt
    retry_backoff_seconds: PositiveFloat


class SchoolSearchSettings(BaseModel):
    postcodes_io_base_url: str
    postcode_cache_ttl_days: PositiveInt
    profile_cache_ttl_seconds: NonNegativeInt
    profile_cache_invalidation_poll_seconds: PositiveFloat


class DataQualitySettings(BaseModel):
    freshness_sla_hours_gias: PositiveInt
    freshness_sla_hours_dfe_characteristics: PositiveInt
    freshness_sla_hours_dfe_attendance: PositiveInt
    freshness_sla_hours_dfe_behaviour: PositiveInt
    freshness_sla_hours_dfe_workforce: PositiveInt
    freshness_sla_hours_dfe_performance: PositiveInt
    freshness_sla_hours_ofsted_latest: PositiveInt
    freshness_sla_hours_ofsted_timeline: PositiveInt
    freshness_sla_hours_ons_imd: PositiveInt
    freshness_sla_hours_uk_house_prices: PositiveInt
    freshness_sla_hours_police_crime_context: PositiveInt
    coverage_drift_threshold: float
    max_consecutive_hard_failures: PositiveInt
    sparse_trend_ratio_threshold: float

    @property
    def source_freshness_sla_hours(self) -> dict[str, float]:
        return {
            "gias": float(self.freshness_sla_hours_gias),
            "dfe_characteristics": float(self.freshness_sla_hours_dfe_characteristics),
            "dfe_attendance": float(self.freshness_sla_hours_dfe_attendance),
            "dfe_behaviour": float(self.freshness_sla_hours_dfe_behaviour),
            "dfe_workforce": float(self.freshness_sla_hours_dfe_workforce),
            "dfe_performance": float(self.freshness_sla_hours_dfe_performance),
            "ofsted_latest": float(self.freshness_sla_hours_ofsted_latest),
            "ofsted_timeline": float(self.freshness_sla_hours_ofsted_timeline),
            "ons_imd": float(self.freshness_sla_hours_ons_imd),
            "uk_house_prices": float(self.freshness_sla_hours_uk_house_prices),
            "police_crime_context": float(self.freshness_sla_hours_police_crime_context),
        }


class AiSettings(BaseModel):
    enabled: bool
    provider: str
    model_id: str
    api_key: str
    api_base_url: str
    batch_size: PositiveInt
    request_timeout_seconds: PositiveFloat
    max_retries: NonNegativeInt
    retry_backoff_seconds: PositiveFloat


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default=DEFAULT_DATABASE_URL,
        min_length=1,
        validation_alias="CIVITAS_DATABASE_URL",
    )

    bronze_root: Path = Field(
        default=DEFAULT_BRONZE_ROOT,
        validation_alias="CIVITAS_BRONZE_ROOT",
    )
    allow_noncanonical_bronze_root: bool = Field(
        default=DEFAULT_ALLOW_NONCANONICAL_BRONZE_ROOT,
        validation_alias="CIVITAS_ALLOW_NONCANONICAL_BRONZE_ROOT",
    )
    gias_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_GIAS_SOURCE_CSV",
    )
    gias_source_zip: str | None = Field(
        default=None,
        validation_alias="CIVITAS_GIAS_SOURCE_ZIP",
    )
    demographics_source_mode: str = Field(
        default=DEFAULT_DEMOGRAPHICS_SOURCE_MODE,
        min_length=1,
        validation_alias="CIVITAS_DEMOGRAPHICS_SOURCE_MODE",
    )
    demographics_spc_publication_slug: str = Field(
        default=DEFAULT_DEMOGRAPHICS_SPC_PUBLICATION_SLUG,
        min_length=1,
        validation_alias="CIVITAS_DEMOGRAPHICS_SPC_PUBLICATION_SLUG",
    )
    demographics_sen_publication_slug: str = Field(
        default=DEFAULT_DEMOGRAPHICS_SEN_PUBLICATION_SLUG,
        min_length=1,
        validation_alias="CIVITAS_DEMOGRAPHICS_SEN_PUBLICATION_SLUG",
    )
    demographics_release_slugs: str | None = Field(
        default=",".join(DEFAULT_DEMOGRAPHICS_RELEASE_SLUGS),
        validation_alias="CIVITAS_DEMOGRAPHICS_RELEASE_SLUGS",
    )
    demographics_lookback_years: PositiveInt = Field(
        default=DEFAULT_DEMOGRAPHICS_LOOKBACK_YEARS,
        validation_alias="CIVITAS_DEMOGRAPHICS_LOOKBACK_YEARS",
    )
    demographics_source_strict_mode: bool = Field(
        default=DEFAULT_DEMOGRAPHICS_SOURCE_STRICT_MODE,
        validation_alias="CIVITAS_DEMOGRAPHICS_SOURCE_STRICT_MODE",
    )
    dfe_attendance_publication_slug: str = Field(
        default=DEFAULT_DFE_ATTENDANCE_PUBLICATION_SLUG,
        min_length=1,
        validation_alias="CIVITAS_DFE_ATTENDANCE_PUBLICATION_SLUG",
    )
    dfe_attendance_release_slugs: str | None = Field(
        default=",".join(DEFAULT_DFE_ATTENDANCE_RELEASE_SLUGS),
        validation_alias="CIVITAS_DFE_ATTENDANCE_RELEASE_SLUGS",
    )
    dfe_attendance_lookback_years: PositiveInt = Field(
        default=DEFAULT_DFE_ATTENDANCE_LOOKBACK_YEARS,
        validation_alias="CIVITAS_DFE_ATTENDANCE_LOOKBACK_YEARS",
    )
    dfe_attendance_source_strict_mode: bool = Field(
        default=DEFAULT_DFE_ATTENDANCE_SOURCE_STRICT_MODE,
        validation_alias="CIVITAS_DFE_ATTENDANCE_SOURCE_STRICT_MODE",
    )
    dfe_behaviour_publication_slug: str = Field(
        default=DEFAULT_DFE_BEHAVIOUR_PUBLICATION_SLUG,
        min_length=1,
        validation_alias="CIVITAS_DFE_BEHAVIOUR_PUBLICATION_SLUG",
    )
    dfe_behaviour_release_slugs: str | None = Field(
        default=",".join(DEFAULT_DFE_BEHAVIOUR_RELEASE_SLUGS),
        validation_alias="CIVITAS_DFE_BEHAVIOUR_RELEASE_SLUGS",
    )
    dfe_behaviour_lookback_years: PositiveInt = Field(
        default=DEFAULT_DFE_BEHAVIOUR_LOOKBACK_YEARS,
        validation_alias="CIVITAS_DFE_BEHAVIOUR_LOOKBACK_YEARS",
    )
    dfe_behaviour_source_strict_mode: bool = Field(
        default=DEFAULT_DFE_BEHAVIOUR_SOURCE_STRICT_MODE,
        validation_alias="CIVITAS_DFE_BEHAVIOUR_SOURCE_STRICT_MODE",
    )
    dfe_workforce_publication_slug: str = Field(
        default=DEFAULT_DFE_WORKFORCE_PUBLICATION_SLUG,
        min_length=1,
        validation_alias="CIVITAS_DFE_WORKFORCE_PUBLICATION_SLUG",
    )
    dfe_workforce_release_slugs: str | None = Field(
        default=",".join(DEFAULT_DFE_WORKFORCE_RELEASE_SLUGS),
        validation_alias="CIVITAS_DFE_WORKFORCE_RELEASE_SLUGS",
    )
    dfe_workforce_lookback_years: PositiveInt = Field(
        default=DEFAULT_DFE_WORKFORCE_LOOKBACK_YEARS,
        validation_alias="CIVITAS_DFE_WORKFORCE_LOOKBACK_YEARS",
    )
    dfe_workforce_source_strict_mode: bool = Field(
        default=DEFAULT_DFE_WORKFORCE_SOURCE_STRICT_MODE,
        validation_alias="CIVITAS_DFE_WORKFORCE_SOURCE_STRICT_MODE",
    )
    dfe_performance_ks2_dataset_id: str = Field(
        default=DEFAULT_DFE_PERFORMANCE_KS2_DATASET_ID,
        min_length=1,
        validation_alias="CIVITAS_DFE_PERFORMANCE_KS2_DATASET_ID",
    )
    dfe_performance_ks4_dataset_id: str = Field(
        default=DEFAULT_DFE_PERFORMANCE_KS4_DATASET_ID,
        min_length=1,
        validation_alias="CIVITAS_DFE_PERFORMANCE_KS4_DATASET_ID",
    )
    dfe_performance_lookback_years: PositiveInt = Field(
        default=DEFAULT_DFE_PERFORMANCE_LOOKBACK_YEARS,
        validation_alias="CIVITAS_DFE_PERFORMANCE_LOOKBACK_YEARS",
    )
    dfe_performance_page_size: PositiveInt = Field(
        default=DEFAULT_DFE_PERFORMANCE_PAGE_SIZE,
        le=10_000,
        validation_alias="CIVITAS_DFE_PERFORMANCE_PAGE_SIZE",
    )
    imd_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_IMD_SOURCE_CSV",
    )
    imd_release: str = Field(
        default=DEFAULT_IMD_RELEASE,
        min_length=1,
        validation_alias="CIVITAS_IMD_RELEASE",
    )
    house_prices_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_HOUSE_PRICES_SOURCE_CSV",
    )
    house_prices_source_url: str | None = Field(
        default=DEFAULT_HOUSE_PRICES_SOURCE_URL,
        validation_alias="CIVITAS_HOUSE_PRICES_SOURCE_URL",
    )
    police_crime_source_archive_url: str | None = Field(
        default=None,
        validation_alias="CIVITAS_POLICE_CRIME_SOURCE_ARCHIVE_URL",
    )
    police_crime_source_mode: str = Field(
        default=DEFAULT_POLICE_CRIME_SOURCE_MODE,
        min_length=1,
        validation_alias="CIVITAS_POLICE_CRIME_SOURCE_MODE",
    )
    police_crime_radius_meters: PositiveFloat = Field(
        default=DEFAULT_POLICE_CRIME_RADIUS_METERS,
        validation_alias="CIVITAS_POLICE_CRIME_RADIUS_METERS",
    )
    ofsted_latest_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_OFSTED_LATEST_SOURCE_CSV",
    )
    ofsted_timeline_source_index_url: str = Field(
        default=DEFAULT_OFSTED_TIMELINE_SOURCE_INDEX_URL,
        min_length=1,
        validation_alias="CIVITAS_OFSTED_TIMELINE_SOURCE_INDEX_URL",
    )
    ofsted_timeline_source_assets: str | None = Field(
        default=None,
        validation_alias="CIVITAS_OFSTED_TIMELINE_SOURCE_ASSETS",
    )
    ofsted_timeline_years: PositiveInt = Field(
        default=DEFAULT_OFSTED_TIMELINE_YEARS,
        validation_alias="CIVITAS_OFSTED_TIMELINE_YEARS",
    )
    ofsted_timeline_include_historical_baseline: bool = Field(
        default=True,
        validation_alias="CIVITAS_OFSTED_TIMELINE_INCLUDE_HISTORICAL_BASELINE",
    )
    pipeline_max_reject_ratio_gias: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_GIAS",
    )
    pipeline_max_reject_ratio_dfe_characteristics: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_CHARACTERISTICS",
    )
    pipeline_max_reject_ratio_dfe_attendance: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_ATTENDANCE",
    )
    pipeline_max_reject_ratio_dfe_behaviour: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_BEHAVIOUR",
    )
    pipeline_max_reject_ratio_dfe_workforce: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_WORKFORCE",
    )
    pipeline_max_reject_ratio_dfe_performance: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_DFE_PERFORMANCE",
    )
    pipeline_max_reject_ratio_ofsted_latest: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_OFSTED_LATEST",
    )
    pipeline_max_reject_ratio_ofsted_timeline: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_OFSTED_TIMELINE",
    )
    pipeline_max_reject_ratio_ons_imd: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_ONS_IMD",
    )
    pipeline_max_reject_ratio_uk_house_prices: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_UK_HOUSE_PRICES",
    )
    pipeline_max_reject_ratio_police_crime_context: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_POLICE_CRIME_CONTEXT",
    )
    pipeline_http_timeout_seconds: PositiveFloat = Field(
        default=DEFAULT_PIPELINE_HTTP_TIMEOUT_SECONDS,
        validation_alias="CIVITAS_PIPELINE_HTTP_TIMEOUT_SECONDS",
    )
    pipeline_max_retries: NonNegativeInt = Field(
        default=DEFAULT_PIPELINE_MAX_RETRIES,
        validation_alias="CIVITAS_PIPELINE_MAX_RETRIES",
    )
    pipeline_retry_backoff_seconds: PositiveFloat = Field(
        default=DEFAULT_PIPELINE_RETRY_BACKOFF_SECONDS,
        validation_alias="CIVITAS_PIPELINE_RETRY_BACKOFF_SECONDS",
    )
    pipeline_stage_chunk_size: PositiveInt = Field(
        default=DEFAULT_PIPELINE_STAGE_CHUNK_SIZE,
        validation_alias="CIVITAS_PIPELINE_STAGE_CHUNK_SIZE",
    )
    pipeline_promote_chunk_size: PositiveInt = Field(
        default=DEFAULT_PIPELINE_PROMOTE_CHUNK_SIZE,
        validation_alias="CIVITAS_PIPELINE_PROMOTE_CHUNK_SIZE",
    )
    pipeline_max_concurrent_sources: PositiveInt = Field(
        default=DEFAULT_PIPELINE_MAX_CONCURRENT_SOURCES,
        validation_alias="CIVITAS_PIPELINE_MAX_CONCURRENT_SOURCES",
    )
    pipeline_resume_enabled: bool = Field(
        default=DEFAULT_PIPELINE_RESUME_ENABLED,
        validation_alias="CIVITAS_PIPELINE_RESUME_ENABLED",
    )

    http_timeout_seconds: PositiveFloat = Field(
        default=10.0,
        validation_alias="CIVITAS_HTTP_TIMEOUT_SECONDS",
    )
    http_max_retries: NonNegativeInt = Field(
        default=2,
        validation_alias="CIVITAS_HTTP_MAX_RETRIES",
    )
    http_retry_backoff_seconds: PositiveFloat = Field(
        default=0.5,
        validation_alias="CIVITAS_HTTP_RETRY_BACKOFF_SECONDS",
    )
    postcodes_io_base_url: str = Field(
        default=DEFAULT_POSTCODES_IO_BASE_URL,
        validation_alias="CIVITAS_POSTCODES_IO_BASE_URL",
    )
    postcode_cache_ttl_days: PositiveInt = Field(
        default=DEFAULT_POSTCODE_CACHE_TTL_DAYS,
        validation_alias="CIVITAS_POSTCODE_CACHE_TTL_DAYS",
    )
    school_profile_cache_ttl_seconds: NonNegativeInt = Field(
        default=DEFAULT_SCHOOL_PROFILE_CACHE_TTL_SECONDS,
        validation_alias="CIVITAS_SCHOOL_PROFILE_CACHE_TTL_SECONDS",
    )
    school_profile_cache_invalidation_poll_seconds: PositiveFloat = Field(
        default=DEFAULT_SCHOOL_PROFILE_CACHE_INVALIDATION_POLL_SECONDS,
        validation_alias="CIVITAS_SCHOOL_PROFILE_CACHE_INVALIDATION_POLL_SECONDS",
    )
    data_quality_freshness_sla_hours_gias: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_GIAS",
    )
    data_quality_freshness_sla_hours_dfe_characteristics: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_CHARACTERISTICS",
    )
    data_quality_freshness_sla_hours_dfe_attendance: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_ATTENDANCE",
    )
    data_quality_freshness_sla_hours_dfe_behaviour: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_BEHAVIOUR",
    )
    data_quality_freshness_sla_hours_dfe_workforce: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_WORKFORCE",
    )
    data_quality_freshness_sla_hours_dfe_performance: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_DFE_PERFORMANCE",
    )
    data_quality_freshness_sla_hours_ofsted_latest: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_OFSTED_LATEST",
    )
    data_quality_freshness_sla_hours_ofsted_timeline: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_OFSTED_TIMELINE",
    )
    data_quality_freshness_sla_hours_ons_imd: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_ONS_IMD",
    )
    data_quality_freshness_sla_hours_uk_house_prices: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_UK_HOUSE_PRICES",
    )
    data_quality_freshness_sla_hours_police_crime_context: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_POLICE_CRIME_CONTEXT",
    )
    data_quality_coverage_drift_threshold: float = Field(
        default=DEFAULT_DATA_QUALITY_COVERAGE_DRIFT_THRESHOLD,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_DATA_QUALITY_COVERAGE_DRIFT_THRESHOLD",
    )
    data_quality_max_consecutive_hard_failures: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_MAX_CONSECUTIVE_HARD_FAILURES,
        validation_alias="CIVITAS_DATA_QUALITY_MAX_CONSECUTIVE_HARD_FAILURES",
    )
    data_quality_sparse_trend_ratio_threshold: float = Field(
        default=DEFAULT_DATA_QUALITY_SPARSE_TREND_RATIO_THRESHOLD,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_DATA_QUALITY_SPARSE_TREND_RATIO_THRESHOLD",
    )
    ai_enabled: bool = Field(
        default=DEFAULT_AI_ENABLED,
        validation_alias="CIVITAS_AI_ENABLED",
    )
    ai_provider: str = Field(
        default=DEFAULT_AI_PROVIDER,
        min_length=1,
        validation_alias="CIVITAS_AI_PROVIDER",
    )
    ai_model_id: str = Field(
        default=DEFAULT_AI_MODEL_ID,
        min_length=1,
        validation_alias="CIVITAS_AI_MODEL_ID",
    )
    ai_api_key: str | None = Field(
        default=None,
        validation_alias="CIVITAS_AI_API_KEY",
    )
    ai_api_base_url: str | None = Field(
        default=DEFAULT_AI_API_BASE_URL,
        validation_alias="CIVITAS_AI_API_BASE_URL",
    )
    ai_batch_size: PositiveInt = Field(
        default=DEFAULT_AI_BATCH_SIZE,
        validation_alias="CIVITAS_AI_BATCH_SIZE",
    )
    ai_request_timeout_seconds: PositiveFloat = Field(
        default=DEFAULT_AI_REQUEST_TIMEOUT_SECONDS,
        validation_alias="CIVITAS_AI_REQUEST_TIMEOUT_SECONDS",
    )
    ai_max_retries: NonNegativeInt = Field(
        default=DEFAULT_AI_MAX_RETRIES,
        validation_alias="CIVITAS_AI_MAX_RETRIES",
    )
    ai_retry_backoff_seconds: PositiveFloat = Field(
        default=DEFAULT_AI_RETRY_BACKOFF_SECONDS,
        validation_alias="CIVITAS_AI_RETRY_BACKOFF_SECONDS",
    )

    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings(url=self.database_url)

    @property
    def pipeline(self) -> PipelineSettings:
        return PipelineSettings(
            bronze_root=self.bronze_root,
            gias_source_csv=self.gias_source_csv,
            gias_source_zip=self.gias_source_zip,
            demographics_source_mode=self.demographics_source_mode,
            demographics_spc_publication_slug=self.demographics_spc_publication_slug,
            demographics_sen_publication_slug=self.demographics_sen_publication_slug,
            demographics_release_slugs=_parse_csv_tokens(self.demographics_release_slugs),
            demographics_lookback_years=self.demographics_lookback_years,
            demographics_source_strict_mode=self.demographics_source_strict_mode,
            dfe_attendance_publication_slug=self.dfe_attendance_publication_slug,
            dfe_attendance_release_slugs=_parse_csv_tokens(self.dfe_attendance_release_slugs),
            dfe_attendance_lookback_years=self.dfe_attendance_lookback_years,
            dfe_attendance_source_strict_mode=self.dfe_attendance_source_strict_mode,
            dfe_behaviour_publication_slug=self.dfe_behaviour_publication_slug,
            dfe_behaviour_release_slugs=_parse_csv_tokens(self.dfe_behaviour_release_slugs),
            dfe_behaviour_lookback_years=self.dfe_behaviour_lookback_years,
            dfe_behaviour_source_strict_mode=self.dfe_behaviour_source_strict_mode,
            dfe_workforce_publication_slug=self.dfe_workforce_publication_slug,
            dfe_workforce_release_slugs=_parse_csv_tokens(self.dfe_workforce_release_slugs),
            dfe_workforce_lookback_years=self.dfe_workforce_lookback_years,
            dfe_workforce_source_strict_mode=self.dfe_workforce_source_strict_mode,
            dfe_performance_ks2_dataset_id=self.dfe_performance_ks2_dataset_id,
            dfe_performance_ks4_dataset_id=self.dfe_performance_ks4_dataset_id,
            dfe_performance_lookback_years=self.dfe_performance_lookback_years,
            dfe_performance_page_size=self.dfe_performance_page_size,
            imd_source_csv=self.imd_source_csv,
            imd_release=self.imd_release,
            house_prices_source_csv=self.house_prices_source_csv,
            house_prices_source_url=self.house_prices_source_url,
            police_crime_source_archive_url=self.police_crime_source_archive_url,
            police_crime_source_mode=self.police_crime_source_mode,
            police_crime_radius_meters=self.police_crime_radius_meters,
            ofsted_latest_source_csv=self.ofsted_latest_source_csv,
            ofsted_timeline_source_index_url=self.ofsted_timeline_source_index_url,
            ofsted_timeline_source_assets=self.ofsted_timeline_source_assets,
            ofsted_timeline_years=self.ofsted_timeline_years,
            ofsted_timeline_include_historical_baseline=(
                self.ofsted_timeline_include_historical_baseline
            ),
            max_reject_ratio_gias=self.pipeline_max_reject_ratio_gias,
            max_reject_ratio_dfe_characteristics=(
                self.pipeline_max_reject_ratio_dfe_characteristics
            ),
            max_reject_ratio_dfe_attendance=self.pipeline_max_reject_ratio_dfe_attendance,
            max_reject_ratio_dfe_behaviour=self.pipeline_max_reject_ratio_dfe_behaviour,
            max_reject_ratio_dfe_workforce=self.pipeline_max_reject_ratio_dfe_workforce,
            max_reject_ratio_dfe_performance=self.pipeline_max_reject_ratio_dfe_performance,
            max_reject_ratio_ofsted_latest=self.pipeline_max_reject_ratio_ofsted_latest,
            max_reject_ratio_ofsted_timeline=self.pipeline_max_reject_ratio_ofsted_timeline,
            max_reject_ratio_ons_imd=self.pipeline_max_reject_ratio_ons_imd,
            max_reject_ratio_uk_house_prices=self.pipeline_max_reject_ratio_uk_house_prices,
            max_reject_ratio_police_crime_context=(
                self.pipeline_max_reject_ratio_police_crime_context
            ),
            http_timeout_seconds=self.pipeline_http_timeout_seconds,
            max_retries=self.pipeline_max_retries,
            retry_backoff_seconds=self.pipeline_retry_backoff_seconds,
            stage_chunk_size=self.pipeline_stage_chunk_size,
            promote_chunk_size=self.pipeline_promote_chunk_size,
            max_concurrent_sources=self.pipeline_max_concurrent_sources,
            resume_enabled=self.pipeline_resume_enabled,
        )

    @property
    def http_clients(self) -> HttpClientSettings:
        return HttpClientSettings(
            timeout_seconds=self.http_timeout_seconds,
            max_retries=self.http_max_retries,
            retry_backoff_seconds=self.http_retry_backoff_seconds,
        )

    @property
    def school_search(self) -> SchoolSearchSettings:
        return SchoolSearchSettings(
            postcodes_io_base_url=self.postcodes_io_base_url,
            postcode_cache_ttl_days=self.postcode_cache_ttl_days,
            profile_cache_ttl_seconds=self.school_profile_cache_ttl_seconds,
            profile_cache_invalidation_poll_seconds=(
                self.school_profile_cache_invalidation_poll_seconds
            ),
        )

    @property
    def data_quality(self) -> DataQualitySettings:
        return DataQualitySettings(
            freshness_sla_hours_gias=self.data_quality_freshness_sla_hours_gias,
            freshness_sla_hours_dfe_characteristics=(
                self.data_quality_freshness_sla_hours_dfe_characteristics
            ),
            freshness_sla_hours_dfe_attendance=self.data_quality_freshness_sla_hours_dfe_attendance,
            freshness_sla_hours_dfe_behaviour=self.data_quality_freshness_sla_hours_dfe_behaviour,
            freshness_sla_hours_dfe_workforce=self.data_quality_freshness_sla_hours_dfe_workforce,
            freshness_sla_hours_dfe_performance=(
                self.data_quality_freshness_sla_hours_dfe_performance
            ),
            freshness_sla_hours_ofsted_latest=self.data_quality_freshness_sla_hours_ofsted_latest,
            freshness_sla_hours_ofsted_timeline=(
                self.data_quality_freshness_sla_hours_ofsted_timeline
            ),
            freshness_sla_hours_ons_imd=self.data_quality_freshness_sla_hours_ons_imd,
            freshness_sla_hours_uk_house_prices=(
                self.data_quality_freshness_sla_hours_uk_house_prices
            ),
            freshness_sla_hours_police_crime_context=(
                self.data_quality_freshness_sla_hours_police_crime_context
            ),
            coverage_drift_threshold=self.data_quality_coverage_drift_threshold,
            max_consecutive_hard_failures=self.data_quality_max_consecutive_hard_failures,
            sparse_trend_ratio_threshold=self.data_quality_sparse_trend_ratio_threshold,
        )

    @property
    def ai(self) -> AiSettings:
        resolved_api_key = self.ai_api_key or ""
        resolved_api_base_url = self.ai_api_base_url or ""
        return AiSettings(
            enabled=self.ai_enabled,
            provider=self.ai_provider,
            model_id=self.ai_model_id,
            api_key=resolved_api_key,
            api_base_url=resolved_api_base_url,
            batch_size=self.ai_batch_size,
            request_timeout_seconds=self.ai_request_timeout_seconds,
            max_retries=self.ai_max_retries,
            retry_backoff_seconds=self.ai_retry_backoff_seconds,
        )

    @field_validator(
        "gias_source_csv",
        "gias_source_zip",
        "demographics_release_slugs",
        "dfe_attendance_release_slugs",
        "dfe_behaviour_release_slugs",
        "dfe_workforce_release_slugs",
        "imd_source_csv",
        "house_prices_source_csv",
        "house_prices_source_url",
        "police_crime_source_archive_url",
        "ofsted_latest_source_csv",
        "ofsted_timeline_source_index_url",
        "ofsted_timeline_source_assets",
        "ai_api_key",
        "ai_api_base_url",
        mode="before",
    )
    @classmethod
    def _empty_string_to_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None
        return value

    @field_validator("ai_provider", mode="before")
    @classmethod
    def _normalize_ai_provider(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized not in {"grok", "openai", "openai_compatible"}:
                raise ValueError(
                    "CIVITAS_AI_PROVIDER must be one of: grok, openai, openai_compatible"
                )
            return normalized
        return value

    @field_validator("ai_model_id", mode="before")
    @classmethod
    def _normalize_ai_model_id(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator(
        "demographics_source_mode",
        "demographics_spc_publication_slug",
        "demographics_sen_publication_slug",
        "dfe_attendance_publication_slug",
        "dfe_behaviour_publication_slug",
        "dfe_workforce_publication_slug",
        "dfe_performance_ks2_dataset_id",
        "dfe_performance_ks4_dataset_id",
        mode="before",
    )
    @classmethod
    def _normalize_demographics_field(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("demographics_source_mode", mode="before")
    @classmethod
    def _normalize_demographics_source_mode(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized != "release_files":
                raise ValueError("CIVITAS_DEMOGRAPHICS_SOURCE_MODE must be one of: release_files")
            return normalized
        return value

    @field_validator("imd_release", mode="before")
    @classmethod
    def _normalize_imd_release(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized in {"iod2025", "iod2019"}:
                return normalized
            raise ValueError("CIVITAS_IMD_RELEASE must be one of: iod2019, iod2025")
        return value

    @field_validator("police_crime_source_mode", mode="before")
    @classmethod
    def _normalize_police_source_mode(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized in {"archive", "api"}:
                return normalized
            raise ValueError("CIVITAS_POLICE_CRIME_SOURCE_MODE must be one of: api, archive")
        return value

    @model_validator(mode="after")
    def _validate_bronze_root(self) -> AppSettings:
        if self.allow_noncanonical_bronze_root:
            return self._validate_ai_settings()

        configured_root = _normalize_config_path(self.bronze_root)
        canonical_root = _normalize_config_path(DEFAULT_BRONZE_ROOT)
        if configured_root != canonical_root:
            raise ValueError(
                "CIVITAS_BRONZE_ROOT must remain at data/bronze unless "
                "CIVITAS_ALLOW_NONCANONICAL_BRONZE_ROOT=true is set for an approved exception."
            )
        return self._validate_ai_settings()

    def _validate_ai_settings(self) -> AppSettings:
        if not self.ai_enabled:
            return self
        if self.ai_api_key is None:
            raise ValueError("CIVITAS_AI_API_KEY must be set when CIVITAS_AI_ENABLED=true.")
        if self.ai_provider == "openai_compatible" and self.ai_api_base_url is None:
            raise ValueError(
                "CIVITAS_AI_API_BASE_URL must be set when CIVITAS_AI_PROVIDER=openai_compatible."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


def _parse_csv_tokens(raw_value: str | None) -> tuple[str, ...]:
    if raw_value is None:
        return ()

    tokens: list[str] = []
    seen: set[str] = set()
    for item in raw_value.split(","):
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        tokens.append(normalized)
    return tuple(tokens)


def _normalize_config_path(path: Path) -> Path:
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    return candidate.resolve(strict=False)
