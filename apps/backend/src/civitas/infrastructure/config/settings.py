from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, NonNegativeInt, PositiveFloat, PositiveInt, field_validator
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
DEFAULT_DFE_PERFORMANCE_KS2_DATASET_ID = "019afee4-e5d0-72f9-9a8f-d7a1a56eac1d"
DEFAULT_DFE_PERFORMANCE_KS4_DATASET_ID = "19e39901-a96c-be76-b9c2-6af54ae076d2"
DEFAULT_DFE_PERFORMANCE_LOOKBACK_YEARS = 3
DEFAULT_DFE_PERFORMANCE_PAGE_SIZE = 10_000
DEFAULT_IMD_RELEASE = "iod2025"
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
    dfe_performance_ks2_dataset_id: str
    dfe_performance_ks4_dataset_id: str
    dfe_performance_lookback_years: PositiveInt
    dfe_performance_page_size: PositiveInt
    imd_source_csv: str | None = None
    imd_release: str
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
    max_reject_ratio_dfe_performance: float
    max_reject_ratio_ofsted_latest: float
    max_reject_ratio_ofsted_timeline: float
    max_reject_ratio_ons_imd: float
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
    freshness_sla_hours_dfe_performance: PositiveInt
    freshness_sla_hours_ofsted_latest: PositiveInt
    freshness_sla_hours_ofsted_timeline: PositiveInt
    freshness_sla_hours_ons_imd: PositiveInt
    freshness_sla_hours_police_crime_context: PositiveInt
    coverage_drift_threshold: float
    max_consecutive_hard_failures: PositiveInt
    sparse_trend_ratio_threshold: float

    @property
    def source_freshness_sla_hours(self) -> dict[str, float]:
        return {
            "gias": float(self.freshness_sla_hours_gias),
            "dfe_characteristics": float(self.freshness_sla_hours_dfe_characteristics),
            "dfe_performance": float(self.freshness_sla_hours_dfe_performance),
            "ofsted_latest": float(self.freshness_sla_hours_ofsted_latest),
            "ofsted_timeline": float(self.freshness_sla_hours_ofsted_timeline),
            "ons_imd": float(self.freshness_sla_hours_ons_imd),
            "police_crime_context": float(self.freshness_sla_hours_police_crime_context),
        }


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
            dfe_performance_ks2_dataset_id=self.dfe_performance_ks2_dataset_id,
            dfe_performance_ks4_dataset_id=self.dfe_performance_ks4_dataset_id,
            dfe_performance_lookback_years=self.dfe_performance_lookback_years,
            dfe_performance_page_size=self.dfe_performance_page_size,
            imd_source_csv=self.imd_source_csv,
            imd_release=self.imd_release,
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
            max_reject_ratio_dfe_performance=self.pipeline_max_reject_ratio_dfe_performance,
            max_reject_ratio_ofsted_latest=self.pipeline_max_reject_ratio_ofsted_latest,
            max_reject_ratio_ofsted_timeline=self.pipeline_max_reject_ratio_ofsted_timeline,
            max_reject_ratio_ons_imd=self.pipeline_max_reject_ratio_ons_imd,
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
            freshness_sla_hours_dfe_performance=(
                self.data_quality_freshness_sla_hours_dfe_performance
            ),
            freshness_sla_hours_ofsted_latest=self.data_quality_freshness_sla_hours_ofsted_latest,
            freshness_sla_hours_ofsted_timeline=(
                self.data_quality_freshness_sla_hours_ofsted_timeline
            ),
            freshness_sla_hours_ons_imd=self.data_quality_freshness_sla_hours_ons_imd,
            freshness_sla_hours_police_crime_context=(
                self.data_quality_freshness_sla_hours_police_crime_context
            ),
            coverage_drift_threshold=self.data_quality_coverage_drift_threshold,
            max_consecutive_hard_failures=self.data_quality_max_consecutive_hard_failures,
            sparse_trend_ratio_threshold=self.data_quality_sparse_trend_ratio_threshold,
        )

    @field_validator(
        "gias_source_csv",
        "gias_source_zip",
        "demographics_release_slugs",
        "imd_source_csv",
        "police_crime_source_archive_url",
        "ofsted_latest_source_csv",
        "ofsted_timeline_source_index_url",
        "ofsted_timeline_source_assets",
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

    @field_validator(
        "demographics_source_mode",
        "demographics_spc_publication_slug",
        "demographics_sen_publication_slug",
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
