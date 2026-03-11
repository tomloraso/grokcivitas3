from __future__ import annotations

from functools import lru_cache
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlparse

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


def _discover_repo_root() -> Path:
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / ".planning" / "project-brief.md").exists():
            return parent
    return Path.cwd().resolve()


REPO_ROOT = _discover_repo_root()
REPO_ENV_FILE = REPO_ROOT / ".env"

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
DEFAULT_SCHOOL_FINANCIAL_BENCHMARKS_WORKBOOK_URLS = (
    "https://financial-benchmarking-and-insights-tool.education.gov.uk/files/"
    "AAR_2023-24_download.xlsx",
)
DEFAULT_SCHOOL_ADMISSIONS_SOURCE_URL = (
    "https://content.explore-education-statistics.service.gov.uk/api/releases/"
    "5ed40264-1835-4848-a29b-446ed6c075c2/files/"
    "7c9894e4-9038-4213-823c-bf50bc993cec"
)
DEFAULT_LEAVER_DESTINATIONS_KS4_RELEASE_PAGE_URL = (
    "https://explore-education-statistics.service.gov.uk/find-statistics/"
    "key-stage-4-destination-measures/2023-24"
)
DEFAULT_LEAVER_DESTINATIONS_KS4_DATA_CATALOGUE_URL = (
    "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/"
    "7be58881-d49f-4e3b-b2b6-0877a1a0fe6e"
)
DEFAULT_LEAVER_DESTINATIONS_KS4_SOURCE_URL = (
    "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/"
    "7be58881-d49f-4e3b-b2b6-0877a1a0fe6e/csv"
)
DEFAULT_LEAVER_DESTINATIONS_16_TO_18_RELEASE_PAGE_URL = (
    "https://explore-education-statistics.service.gov.uk/find-statistics/"
    "16-18-destination-measures/2023-24"
)
DEFAULT_LEAVER_DESTINATIONS_16_TO_18_DATA_CATALOGUE_URL = (
    "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/"
    "bbee3278-589b-436f-a031-adeb0368e49f"
)
DEFAULT_LEAVER_DESTINATIONS_16_TO_18_SOURCE_URL = (
    "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/"
    "bbee3278-589b-436f-a031-adeb0368e49f/csv"
)
DEFAULT_KS4_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL = (
    "https://explore-education-statistics.service.gov.uk/find-statistics/key-stage-4-performance"
)
DEFAULT_KS4_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL = (
    "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/"
    "49abed18-1c61-489f-afc0-11f501335da1"
)
DEFAULT_KS4_SUBJECT_PERFORMANCE_SOURCE_URL = (
    "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/"
    "49abed18-1c61-489f-afc0-11f501335da1/csv"
)
DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL = (
    "https://explore-education-statistics.service.gov.uk/find-statistics/"
    "a-level-and-other-16-to-18-results"
)
DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL = (
    "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/"
    "9a275c77-4325-4ac8-aa9e-b1a2bd3ab63b"
)
DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_SOURCE_URL = (
    "https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/"
    "9a275c77-4325-4ac8-aa9e-b1a2bd3ab63b/csv"
)
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
DEFAULT_RUNTIME_ENVIRONMENT = "local"
DEFAULT_AUTH_PROVIDER = "development"
DEFAULT_AUTH_SESSION_COOKIE_NAME = "civitas_session"
DEFAULT_AUTH_SESSION_COOKIE_SECURE = False
DEFAULT_AUTH_SESSION_COOKIE_SAMESITE = "lax"
DEFAULT_AUTH_SESSION_TTL_HOURS = 24 * 14
DEFAULT_AUTH_STATE_TTL_MINUTES = 15
DEFAULT_AUTH_CALLBACK_ERROR_PATH = "/sign-in"
DEFAULT_AUTH_ALLOWED_ORIGINS = ",".join(
    (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://testserver",
    )
)
DEFAULT_AUTH_SHARED_SECRET = "civitas-local-dev-shared-secret"
DEFAULT_AUTH_AUTH0_CONNECTION = "email"
DEFAULT_BILLING_ENABLED = False
DEFAULT_BILLING_PROVIDER = "stripe"


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
    school_admissions_source_csv: str | None = None
    school_admissions_source_url: str | None = None
    leaver_destinations_ks4_source_csv: str | None = None
    leaver_destinations_ks4_source_url: str
    leaver_destinations_ks4_release_page_url: str
    leaver_destinations_ks4_data_catalogue_url: str
    leaver_destinations_16_to_18_source_csv: str | None = None
    leaver_destinations_16_to_18_source_url: str
    leaver_destinations_16_to_18_release_page_url: str
    leaver_destinations_16_to_18_data_catalogue_url: str
    ks4_subject_performance_source_csv: str | None = None
    ks4_subject_performance_source_url: str
    ks4_subject_performance_release_page_url: str
    ks4_subject_performance_data_catalogue_url: str
    sixteen_to_eighteen_subject_performance_source_csv: str | None = None
    sixteen_to_eighteen_subject_performance_source_url: str
    sixteen_to_eighteen_subject_performance_release_page_url: str
    sixteen_to_eighteen_subject_performance_data_catalogue_url: str
    school_financial_benchmarks_workbook_urls: tuple[str, ...]
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
    max_reject_ratio_school_admissions: float
    max_reject_ratio_leaver_destinations: float
    max_reject_ratio_ks4_subject_performance: float
    max_reject_ratio_sixteen_to_eighteen_subject_performance: float
    max_reject_ratio_school_financial_benchmarks: float
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
    freshness_sla_hours_school_admissions: PositiveInt
    freshness_sla_hours_leaver_destinations: PositiveInt
    freshness_sla_hours_ks4_subject_performance: PositiveInt
    freshness_sla_hours_sixteen_to_eighteen_subject_performance: PositiveInt
    freshness_sla_hours_school_financial_benchmarks: PositiveInt
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
            "school_admissions": float(self.freshness_sla_hours_school_admissions),
            "leaver_destinations": float(self.freshness_sla_hours_leaver_destinations),
            "ks4_subject_performance": float(self.freshness_sla_hours_ks4_subject_performance),
            "sixteen_to_eighteen_subject_performance": float(
                self.freshness_sla_hours_sixteen_to_eighteen_subject_performance
            ),
            "school_financial_benchmarks": float(
                self.freshness_sla_hours_school_financial_benchmarks
            ),
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


class AuthSettings(BaseModel):
    provider: str
    session_cookie_name: str
    session_cookie_secure: bool
    session_cookie_samesite: str
    session_ttl_hours: PositiveInt
    state_ttl_minutes: PositiveInt
    callback_error_path: str
    allowed_origins: tuple[str, ...]
    shared_secret: str
    auth0: "Auth0ProviderSettings | None"


class Auth0ProviderSettings(BaseModel):
    domain: str
    client_id: str
    client_secret: str
    audience: str | None = None
    connection: str | None = None


class BillingSettings(BaseModel):
    enabled: bool
    provider: str
    stripe: "StripeBillingSettings | None"


class StripeBillingSettings(BaseModel):
    secret_key: str
    webhook_secret: str
    portal_configuration_id: str | None = None


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default=DEFAULT_DATABASE_URL,
        min_length=1,
        validation_alias="CIVITAS_DATABASE_URL",
    )
    test_database_url: str | None = Field(
        default=None,
        validation_alias="CIVITAS_TEST_DATABASE_URL",
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
    school_admissions_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_SCHOOL_ADMISSIONS_SOURCE_CSV",
    )
    school_admissions_source_url: str | None = Field(
        default=DEFAULT_SCHOOL_ADMISSIONS_SOURCE_URL,
        validation_alias="CIVITAS_SCHOOL_ADMISSIONS_SOURCE_URL",
    )
    leaver_destinations_ks4_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_LEAVER_DESTINATIONS_KS4_SOURCE_CSV",
    )
    leaver_destinations_ks4_source_url: str = Field(
        default=DEFAULT_LEAVER_DESTINATIONS_KS4_SOURCE_URL,
        validation_alias="CIVITAS_LEAVER_DESTINATIONS_KS4_SOURCE_URL",
    )
    leaver_destinations_ks4_release_page_url: str = Field(
        default=DEFAULT_LEAVER_DESTINATIONS_KS4_RELEASE_PAGE_URL,
        validation_alias="CIVITAS_LEAVER_DESTINATIONS_KS4_RELEASE_PAGE_URL",
    )
    leaver_destinations_ks4_data_catalogue_url: str = Field(
        default=DEFAULT_LEAVER_DESTINATIONS_KS4_DATA_CATALOGUE_URL,
        validation_alias="CIVITAS_LEAVER_DESTINATIONS_KS4_DATA_CATALOGUE_URL",
    )
    leaver_destinations_16_to_18_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_LEAVER_DESTINATIONS_16_TO_18_SOURCE_CSV",
    )
    leaver_destinations_16_to_18_source_url: str = Field(
        default=DEFAULT_LEAVER_DESTINATIONS_16_TO_18_SOURCE_URL,
        validation_alias="CIVITAS_LEAVER_DESTINATIONS_16_TO_18_SOURCE_URL",
    )
    leaver_destinations_16_to_18_release_page_url: str = Field(
        default=DEFAULT_LEAVER_DESTINATIONS_16_TO_18_RELEASE_PAGE_URL,
        validation_alias="CIVITAS_LEAVER_DESTINATIONS_16_TO_18_RELEASE_PAGE_URL",
    )
    leaver_destinations_16_to_18_data_catalogue_url: str = Field(
        default=DEFAULT_LEAVER_DESTINATIONS_16_TO_18_DATA_CATALOGUE_URL,
        validation_alias="CIVITAS_LEAVER_DESTINATIONS_16_TO_18_DATA_CATALOGUE_URL",
    )
    ks4_subject_performance_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_KS4_SUBJECT_PERFORMANCE_SOURCE_CSV",
    )
    ks4_subject_performance_source_url: str = Field(
        default=DEFAULT_KS4_SUBJECT_PERFORMANCE_SOURCE_URL,
        validation_alias="CIVITAS_KS4_SUBJECT_PERFORMANCE_SOURCE_URL",
    )
    ks4_subject_performance_release_page_url: str = Field(
        default=DEFAULT_KS4_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL,
        validation_alias="CIVITAS_KS4_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL",
    )
    ks4_subject_performance_data_catalogue_url: str = Field(
        default=DEFAULT_KS4_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL,
        validation_alias="CIVITAS_KS4_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL",
    )
    sixteen_to_eighteen_subject_performance_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_SOURCE_CSV",
    )
    sixteen_to_eighteen_subject_performance_source_url: str = Field(
        default=DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_SOURCE_URL,
        validation_alias="CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_SOURCE_URL",
    )
    sixteen_to_eighteen_subject_performance_release_page_url: str = Field(
        default=DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL,
        validation_alias="CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_RELEASE_PAGE_URL",
    )
    sixteen_to_eighteen_subject_performance_data_catalogue_url: str = Field(
        default=DEFAULT_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL,
        validation_alias="CIVITAS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE_DATA_CATALOGUE_URL",
    )
    school_financial_benchmarks_workbook_urls: str | None = Field(
        default=",".join(DEFAULT_SCHOOL_FINANCIAL_BENCHMARKS_WORKBOOK_URLS),
        validation_alias="CIVITAS_SCHOOL_FINANCIAL_BENCHMARKS_WORKBOOK_URLS",
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
    pipeline_max_reject_ratio_school_admissions: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_SCHOOL_ADMISSIONS",
    )
    pipeline_max_reject_ratio_leaver_destinations: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_LEAVER_DESTINATIONS",
    )
    pipeline_max_reject_ratio_ks4_subject_performance: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_KS4_SUBJECT_PERFORMANCE",
    )
    pipeline_max_reject_ratio_sixteen_to_eighteen_subject_performance: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias=(
            "CIVITAS_PIPELINE_MAX_REJECT_RATIO_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE"
        ),
    )
    pipeline_max_reject_ratio_school_financial_benchmarks: float = Field(
        default=DEFAULT_PIPELINE_MAX_REJECT_RATIO,
        ge=0.0,
        le=1.0,
        validation_alias="CIVITAS_PIPELINE_MAX_REJECT_RATIO_SCHOOL_FINANCIAL_BENCHMARKS",
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
    data_quality_freshness_sla_hours_school_admissions: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_SCHOOL_ADMISSIONS",
    )
    data_quality_freshness_sla_hours_leaver_destinations: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_LEAVER_DESTINATIONS",
    )
    data_quality_freshness_sla_hours_ks4_subject_performance: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias="CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_KS4_SUBJECT_PERFORMANCE",
    )
    data_quality_freshness_sla_hours_sixteen_to_eighteen_subject_performance: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias=(
            "CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_SIXTEEN_TO_EIGHTEEN_SUBJECT_PERFORMANCE"
        ),
    )
    data_quality_freshness_sla_hours_school_financial_benchmarks: PositiveInt = Field(
        default=DEFAULT_DATA_QUALITY_FRESHNESS_SLA_HOURS,
        validation_alias=("CIVITAS_DATA_QUALITY_FRESHNESS_SLA_HOURS_SCHOOL_FINANCIAL_BENCHMARKS"),
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
    runtime_environment: str = Field(
        default=DEFAULT_RUNTIME_ENVIRONMENT,
        validation_alias="CIVITAS_RUNTIME_ENVIRONMENT",
    )
    auth_provider: str = Field(
        default=DEFAULT_AUTH_PROVIDER,
        validation_alias="CIVITAS_AUTH_PROVIDER",
    )
    auth_session_cookie_name: str = Field(
        default=DEFAULT_AUTH_SESSION_COOKIE_NAME,
        validation_alias="CIVITAS_AUTH_SESSION_COOKIE_NAME",
        min_length=1,
    )
    auth_session_cookie_secure: bool = Field(
        default=DEFAULT_AUTH_SESSION_COOKIE_SECURE,
        validation_alias="CIVITAS_AUTH_SESSION_COOKIE_SECURE",
    )
    auth_session_cookie_samesite: str = Field(
        default=DEFAULT_AUTH_SESSION_COOKIE_SAMESITE,
        validation_alias="CIVITAS_AUTH_SESSION_COOKIE_SAMESITE",
        min_length=1,
    )
    auth_session_ttl_hours: PositiveInt = Field(
        default=DEFAULT_AUTH_SESSION_TTL_HOURS,
        validation_alias="CIVITAS_AUTH_SESSION_TTL_HOURS",
    )
    auth_state_ttl_minutes: PositiveInt = Field(
        default=DEFAULT_AUTH_STATE_TTL_MINUTES,
        validation_alias="CIVITAS_AUTH_STATE_TTL_MINUTES",
    )
    auth_callback_error_path: str = Field(
        default=DEFAULT_AUTH_CALLBACK_ERROR_PATH,
        validation_alias="CIVITAS_AUTH_CALLBACK_ERROR_PATH",
        min_length=1,
    )
    auth_allowed_origins: str | None = Field(
        default=DEFAULT_AUTH_ALLOWED_ORIGINS,
        validation_alias="CIVITAS_AUTH_ALLOWED_ORIGINS",
    )
    auth_shared_secret: str = Field(
        default=DEFAULT_AUTH_SHARED_SECRET,
        validation_alias="CIVITAS_AUTH_SHARED_SECRET",
        min_length=1,
    )
    auth_auth0_domain: str | None = Field(
        default=None,
        validation_alias="CIVITAS_AUTH_AUTH0_DOMAIN",
    )
    auth_auth0_client_id: str | None = Field(
        default=None,
        validation_alias="CIVITAS_AUTH_AUTH0_CLIENT_ID",
    )
    auth_auth0_client_secret: str | None = Field(
        default=None,
        validation_alias="CIVITAS_AUTH_AUTH0_CLIENT_SECRET",
    )
    auth_auth0_audience: str | None = Field(
        default=None,
        validation_alias="CIVITAS_AUTH_AUTH0_AUDIENCE",
    )
    auth_auth0_connection: str | None = Field(
        default=DEFAULT_AUTH_AUTH0_CONNECTION,
        validation_alias="CIVITAS_AUTH_AUTH0_CONNECTION",
    )
    billing_enabled: bool = Field(
        default=DEFAULT_BILLING_ENABLED,
        validation_alias="CIVITAS_BILLING_ENABLED",
    )
    billing_provider: str = Field(
        default=DEFAULT_BILLING_PROVIDER,
        validation_alias="CIVITAS_BILLING_PROVIDER",
    )
    billing_stripe_secret_key: str | None = Field(
        default=None,
        validation_alias="CIVITAS_BILLING_STRIPE_SECRET_KEY",
    )
    billing_stripe_webhook_secret: str | None = Field(
        default=None,
        validation_alias="CIVITAS_BILLING_STRIPE_WEBHOOK_SECRET",
    )
    billing_stripe_portal_configuration_id: str | None = Field(
        default=None,
        validation_alias="CIVITAS_BILLING_STRIPE_PORTAL_CONFIGURATION_ID",
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
            school_admissions_source_csv=self.school_admissions_source_csv,
            school_admissions_source_url=self.school_admissions_source_url,
            leaver_destinations_ks4_source_csv=self.leaver_destinations_ks4_source_csv,
            leaver_destinations_ks4_source_url=self.leaver_destinations_ks4_source_url,
            leaver_destinations_ks4_release_page_url=(
                self.leaver_destinations_ks4_release_page_url
            ),
            leaver_destinations_ks4_data_catalogue_url=(
                self.leaver_destinations_ks4_data_catalogue_url
            ),
            leaver_destinations_16_to_18_source_csv=(self.leaver_destinations_16_to_18_source_csv),
            leaver_destinations_16_to_18_source_url=(self.leaver_destinations_16_to_18_source_url),
            leaver_destinations_16_to_18_release_page_url=(
                self.leaver_destinations_16_to_18_release_page_url
            ),
            leaver_destinations_16_to_18_data_catalogue_url=(
                self.leaver_destinations_16_to_18_data_catalogue_url
            ),
            ks4_subject_performance_source_csv=self.ks4_subject_performance_source_csv,
            ks4_subject_performance_source_url=self.ks4_subject_performance_source_url,
            ks4_subject_performance_release_page_url=(
                self.ks4_subject_performance_release_page_url
            ),
            ks4_subject_performance_data_catalogue_url=(
                self.ks4_subject_performance_data_catalogue_url
            ),
            sixteen_to_eighteen_subject_performance_source_csv=(
                self.sixteen_to_eighteen_subject_performance_source_csv
            ),
            sixteen_to_eighteen_subject_performance_source_url=(
                self.sixteen_to_eighteen_subject_performance_source_url
            ),
            sixteen_to_eighteen_subject_performance_release_page_url=(
                self.sixteen_to_eighteen_subject_performance_release_page_url
            ),
            sixteen_to_eighteen_subject_performance_data_catalogue_url=(
                self.sixteen_to_eighteen_subject_performance_data_catalogue_url
            ),
            school_financial_benchmarks_workbook_urls=_parse_csv_tokens(
                self.school_financial_benchmarks_workbook_urls
            ),
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
            max_reject_ratio_school_admissions=self.pipeline_max_reject_ratio_school_admissions,
            max_reject_ratio_leaver_destinations=(
                self.pipeline_max_reject_ratio_leaver_destinations
            ),
            max_reject_ratio_ks4_subject_performance=(
                self.pipeline_max_reject_ratio_ks4_subject_performance
            ),
            max_reject_ratio_sixteen_to_eighteen_subject_performance=(
                self.pipeline_max_reject_ratio_sixteen_to_eighteen_subject_performance
            ),
            max_reject_ratio_school_financial_benchmarks=(
                self.pipeline_max_reject_ratio_school_financial_benchmarks
            ),
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
            freshness_sla_hours_school_admissions=(
                self.data_quality_freshness_sla_hours_school_admissions
            ),
            freshness_sla_hours_leaver_destinations=(
                self.data_quality_freshness_sla_hours_leaver_destinations
            ),
            freshness_sla_hours_ks4_subject_performance=(
                self.data_quality_freshness_sla_hours_ks4_subject_performance
            ),
            freshness_sla_hours_sixteen_to_eighteen_subject_performance=(
                self.data_quality_freshness_sla_hours_sixteen_to_eighteen_subject_performance
            ),
            freshness_sla_hours_school_financial_benchmarks=(
                self.data_quality_freshness_sla_hours_school_financial_benchmarks
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

    @property
    def auth(self) -> AuthSettings:
        return AuthSettings(
            provider=self.auth_provider,
            session_cookie_name=self.auth_session_cookie_name,
            session_cookie_secure=self.auth_session_cookie_secure,
            session_cookie_samesite=self.auth_session_cookie_samesite,
            session_ttl_hours=self.auth_session_ttl_hours,
            state_ttl_minutes=self.auth_state_ttl_minutes,
            callback_error_path=self.auth_callback_error_path,
            allowed_origins=_parse_origin_tokens(self.auth_allowed_origins),
            shared_secret=self.auth_shared_secret,
            auth0=self._build_auth0_settings(),
        )

    @property
    def billing(self) -> BillingSettings:
        return BillingSettings(
            enabled=self.billing_enabled,
            provider=self.billing_provider,
            stripe=self._build_stripe_billing_settings(),
        )

    @field_validator(
        "gias_source_csv",
        "gias_source_zip",
        "demographics_release_slugs",
        "dfe_attendance_release_slugs",
        "dfe_behaviour_release_slugs",
        "dfe_workforce_release_slugs",
        "school_admissions_source_csv",
        "school_admissions_source_url",
        "leaver_destinations_ks4_source_csv",
        "leaver_destinations_ks4_source_url",
        "leaver_destinations_ks4_release_page_url",
        "leaver_destinations_ks4_data_catalogue_url",
        "leaver_destinations_16_to_18_source_csv",
        "leaver_destinations_16_to_18_source_url",
        "leaver_destinations_16_to_18_release_page_url",
        "leaver_destinations_16_to_18_data_catalogue_url",
        "ks4_subject_performance_source_csv",
        "ks4_subject_performance_source_url",
        "ks4_subject_performance_release_page_url",
        "ks4_subject_performance_data_catalogue_url",
        "sixteen_to_eighteen_subject_performance_source_csv",
        "sixteen_to_eighteen_subject_performance_source_url",
        "sixteen_to_eighteen_subject_performance_release_page_url",
        "sixteen_to_eighteen_subject_performance_data_catalogue_url",
        "school_financial_benchmarks_workbook_urls",
        "imd_source_csv",
        "house_prices_source_csv",
        "house_prices_source_url",
        "police_crime_source_archive_url",
        "ofsted_latest_source_csv",
        "ofsted_timeline_source_index_url",
        "ofsted_timeline_source_assets",
        "ai_api_key",
        "ai_api_base_url",
        "auth_allowed_origins",
        "auth_session_cookie_name",
        "auth_callback_error_path",
        "auth_shared_secret",
        "auth_auth0_domain",
        "auth_auth0_client_id",
        "auth_auth0_client_secret",
        "auth_auth0_audience",
        "auth_auth0_connection",
        "test_database_url",
        "billing_stripe_secret_key",
        "billing_stripe_webhook_secret",
        "billing_stripe_portal_configuration_id",
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

    @field_validator("runtime_environment", mode="before")
    @classmethod
    def _normalize_runtime_environment(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized not in {"local", "test", "staging", "production"}:
                raise ValueError(
                    "CIVITAS_RUNTIME_ENVIRONMENT must be one of: local, test, staging, production"
                )
            return normalized
        return value

    @field_validator("auth_provider", mode="before")
    @classmethod
    def _normalize_auth_provider(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized not in {"development", "auth0"}:
                raise ValueError("CIVITAS_AUTH_PROVIDER must be one of: auth0, development")
            return normalized
        return value

    @field_validator("billing_provider", mode="before")
    @classmethod
    def _normalize_billing_provider(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized != "stripe":
                raise ValueError("CIVITAS_BILLING_PROVIDER must be one of: stripe")
            return normalized
        return value

    @field_validator("auth_session_cookie_name", mode="before")
    @classmethod
    def _normalize_auth_cookie_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("auth_session_cookie_samesite", mode="before")
    @classmethod
    def _normalize_auth_cookie_samesite(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized not in {"lax", "strict", "none"}:
                raise ValueError(
                    "CIVITAS_AUTH_SESSION_COOKIE_SAMESITE must be one of: lax, strict, none"
                )
            return normalized
        return value

    @field_validator("auth_callback_error_path", mode="before")
    @classmethod
    def _normalize_auth_callback_error_path(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized.startswith("/") or normalized.startswith("//"):
                raise ValueError("CIVITAS_AUTH_CALLBACK_ERROR_PATH must start with a single /")
            return normalized
        return value

    @field_validator("auth_allowed_origins", mode="before")
    @classmethod
    def _normalize_auth_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            try:
                return ",".join(_parse_origin_tokens(value))
            except ValueError as exc:
                raise ValueError(
                    "CIVITAS_AUTH_ALLOWED_ORIGINS must contain a comma-separated list of valid origins."
                ) from exc
        return value

    @field_validator("auth_shared_secret", mode="before")
    @classmethod
    def _normalize_auth_shared_secret(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("auth_auth0_domain", mode="before")
    @classmethod
    def _normalize_auth0_domain(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        candidate = value.strip().casefold()
        if not candidate:
            return None
        if "://" in candidate or "/" in candidate or "?" in candidate or "#" in candidate:
            raise ValueError(
                "CIVITAS_AUTH_AUTH0_DOMAIN must be a bare Auth0 domain or custom host without scheme or path."
            )

        parsed = urlparse(f"https://{candidate}")
        if (
            not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "CIVITAS_AUTH_AUTH0_DOMAIN must be a bare Auth0 domain or custom host without scheme or path."
            )
        return parsed.netloc.casefold()

    @field_validator(
        "auth_auth0_client_id",
        "auth_auth0_client_secret",
        "auth_auth0_audience",
        "auth_auth0_connection",
        mode="before",
    )
    @classmethod
    def _normalize_auth0_text_field(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
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
            return self._validate_auth_settings()
        if self.ai_api_key is None:
            raise ValueError("CIVITAS_AI_API_KEY must be set when CIVITAS_AI_ENABLED=true.")
        if self.ai_provider == "openai_compatible" and self.ai_api_base_url is None:
            raise ValueError(
                "CIVITAS_AI_API_BASE_URL must be set when CIVITAS_AI_PROVIDER=openai_compatible."
            )
        return self._validate_auth_settings()

    def _validate_auth_settings(self) -> AppSettings:
        if not self.auth.allowed_origins:
            raise ValueError(
                "CIVITAS_AUTH_ALLOWED_ORIGINS must contain at least one allowed origin."
            )

        if self.auth_session_cookie_samesite == "none" and not self.auth_session_cookie_secure:
            raise ValueError(
                "CIVITAS_AUTH_SESSION_COOKIE_SECURE must be true when "
                "CIVITAS_AUTH_SESSION_COOKIE_SAMESITE=none."
            )

        if self.auth_provider == "development":
            if self.runtime_environment not in {"local", "test"}:
                raise ValueError(
                    "CIVITAS_AUTH_PROVIDER=development is only allowed in local or test environments."
                )
            if any(not _is_local_auth_origin(origin) for origin in self.auth.allowed_origins):
                raise ValueError(
                    "CIVITAS_AUTH_PROVIDER=development requires localhost, loopback, or "
                    "testserver auth allowed origins."
                )
        if self.auth_provider == "auth0" and (
            self.auth_auth0_domain is None
            or self.auth_auth0_client_id is None
            or self.auth_auth0_client_secret is None
        ):
            raise ValueError(
                "CIVITAS_AUTH_AUTH0_DOMAIN, CIVITAS_AUTH_AUTH0_CLIENT_ID, and "
                "CIVITAS_AUTH_AUTH0_CLIENT_SECRET must be set when "
                "CIVITAS_AUTH_PROVIDER=auth0."
            )

        if self.runtime_environment in {"staging", "production"}:
            if not self.auth_session_cookie_secure:
                raise ValueError(
                    "CIVITAS_AUTH_SESSION_COOKIE_SECURE must be true in staging or production."
                )
            if self.auth_shared_secret == DEFAULT_AUTH_SHARED_SECRET:
                raise ValueError(
                    "CIVITAS_AUTH_SHARED_SECRET must be overridden outside local or test environments."
                )

        return self._validate_billing_settings()

    def _validate_billing_settings(self) -> AppSettings:
        if not self.billing_enabled:
            return self

        if self.billing_provider == "stripe" and (
            self.billing_stripe_secret_key is None or self.billing_stripe_webhook_secret is None
        ):
            raise ValueError(
                "CIVITAS_BILLING_STRIPE_SECRET_KEY and CIVITAS_BILLING_STRIPE_WEBHOOK_SECRET "
                "must be set when CIVITAS_BILLING_ENABLED=true."
            )

        return self

    def _build_auth0_settings(self) -> Auth0ProviderSettings | None:
        if (
            self.auth_provider != "auth0"
            or self.auth_auth0_domain is None
            or self.auth_auth0_client_id is None
            or self.auth_auth0_client_secret is None
        ):
            return None

        return Auth0ProviderSettings(
            domain=self.auth_auth0_domain,
            client_id=self.auth_auth0_client_id,
            client_secret=self.auth_auth0_client_secret,
            audience=self.auth_auth0_audience,
            connection=self.auth_auth0_connection or DEFAULT_AUTH_AUTH0_CONNECTION,
        )

    def _build_stripe_billing_settings(self) -> StripeBillingSettings | None:
        if (
            self.billing_provider != "stripe"
            or self.billing_stripe_secret_key is None
            or self.billing_stripe_webhook_secret is None
        ):
            return None

        return StripeBillingSettings(
            secret_key=self.billing_stripe_secret_key,
            webhook_secret=self.billing_stripe_webhook_secret,
            portal_configuration_id=self.billing_stripe_portal_configuration_id,
        )


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


def _parse_origin_tokens(raw_value: str | None) -> tuple[str, ...]:
    if raw_value is None:
        return ()

    tokens: list[str] = []
    seen: set[str] = set()
    for item in raw_value.split(","):
        normalized = _normalize_origin(item)
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        tokens.append(normalized)
    return tuple(tokens)


def _normalize_origin(value: str) -> str | None:
    candidate = value.strip()
    if not candidate:
        return None

    parsed = urlparse(candidate)
    if (
        not parsed.scheme
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("origin must be scheme + host (+ optional port)")

    return f"{parsed.scheme.casefold()}://{parsed.netloc.casefold()}"


def _is_local_auth_origin(origin: str) -> bool:
    parsed = urlparse(origin)
    host = parsed.hostname
    if host in {"localhost", "testserver"}:
        return True
    if host is None:
        return False

    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def _normalize_config_path(path: Path) -> Path:
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    return candidate.resolve(strict=False)
