from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, NonNegativeInt, PositiveFloat, PositiveInt, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "postgresql+psycopg://app:app@localhost:5432/app"
DEFAULT_BRONZE_ROOT = Path("data/bronze")
DEFAULT_DFE_CHARACTERISTICS_DATASET_ID = "019afee4-ba17-73cb-85e0-f88c101bb734"
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
    ofsted_latest_source_csv: str | None = None


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
    ofsted_latest_source_csv: str | None = Field(
        default=None,
        validation_alias="CIVITAS_OFSTED_LATEST_SOURCE_CSV",
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
            ofsted_latest_source_csv=self.ofsted_latest_source_csv,
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
        "ofsted_latest_source_csv",
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


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
