from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, NonNegativeInt, PositiveFloat, PositiveInt, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+psycopg://app:app@localhost:5432/app"
DEFAULT_BRONZE_ROOT = Path("data/bronze")
DEFAULT_DFE_CHARACTERISTICS_DATASET_ID = "019afee4-ba17-73cb-85e0-f88c101bb734"
DEFAULT_IMD_RELEASE = "iod2025"
DEFAULT_POLICE_CRIME_SOURCE_MODE = "archive"
DEFAULT_POLICE_CRIME_RADIUS_METERS = 1609.344
DEFAULT_OFSTED_TIMELINE_SOURCE_INDEX_URL = (
    "https://www.gov.uk/government/statistical-data-sets/"
    "monthly-management-information-ofsteds-school-inspections-outcomes"
)
DEFAULT_POSTCODES_IO_BASE_URL = "https://api.postcodes.io"
DEFAULT_POSTCODE_CACHE_TTL_DAYS = 30


class DatabaseSettings(BaseModel):
    url: str


class PipelineSettings(BaseModel):
    bronze_root: Path
    gias_source_csv: str | None = None
    gias_source_zip: str | None = None
    dfe_characteristics_source_csv: str | None = None
    dfe_characteristics_dataset_id: str
    imd_source_csv: str | None = None
    imd_release: str
    police_crime_source_archive_url: str | None = None
    police_crime_source_mode: str
    police_crime_radius_meters: PositiveFloat
    ofsted_latest_source_csv: str | None = None
    ofsted_timeline_source_index_url: str
    ofsted_timeline_source_assets: str | None = None
    ofsted_timeline_include_historical_baseline: bool = True


class HttpClientSettings(BaseModel):
    timeout_seconds: PositiveFloat
    max_retries: NonNegativeInt
    retry_backoff_seconds: PositiveFloat


class SchoolSearchSettings(BaseModel):
    postcodes_io_base_url: str
    postcode_cache_ttl_days: PositiveInt


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
    dfe_characteristics_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_DFE_CHARACTERISTICS_SOURCE_CSV",
    )
    dfe_characteristics_dataset_id: str = Field(
        default=DEFAULT_DFE_CHARACTERISTICS_DATASET_ID,
        min_length=1,
        validation_alias="CIVITAS_DFE_CHARACTERISTICS_DATASET_ID",
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
    ofsted_timeline_include_historical_baseline: bool = Field(
        default=True,
        validation_alias="CIVITAS_OFSTED_TIMELINE_INCLUDE_HISTORICAL_BASELINE",
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

    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings(url=self.database_url)

    @property
    def pipeline(self) -> PipelineSettings:
        return PipelineSettings(
            bronze_root=self.bronze_root,
            gias_source_csv=self.gias_source_csv,
            gias_source_zip=self.gias_source_zip,
            dfe_characteristics_source_csv=self.dfe_characteristics_source_csv,
            dfe_characteristics_dataset_id=self.dfe_characteristics_dataset_id,
            imd_source_csv=self.imd_source_csv,
            imd_release=self.imd_release,
            police_crime_source_archive_url=self.police_crime_source_archive_url,
            police_crime_source_mode=self.police_crime_source_mode,
            police_crime_radius_meters=self.police_crime_radius_meters,
            ofsted_latest_source_csv=self.ofsted_latest_source_csv,
            ofsted_timeline_source_index_url=self.ofsted_timeline_source_index_url,
            ofsted_timeline_source_assets=self.ofsted_timeline_source_assets,
            ofsted_timeline_include_historical_baseline=(
                self.ofsted_timeline_include_historical_baseline
            ),
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
        )

    @field_validator(
        "gias_source_csv",
        "gias_source_zip",
        "dfe_characteristics_source_csv",
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

    @field_validator("dfe_characteristics_dataset_id", mode="before")
    @classmethod
    def _normalize_dataset_id(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
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
