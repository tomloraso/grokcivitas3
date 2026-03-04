from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SchoolTrendPointResponse(BaseModel):
    academic_year: str
    value: float | None
    delta: float | None
    direction: Literal["up", "down", "flat"] | None


class SchoolTrendsSeriesResponse(BaseModel):
    disadvantaged_pct: list[SchoolTrendPointResponse]
    sen_pct: list[SchoolTrendPointResponse]
    ehcp_pct: list[SchoolTrendPointResponse]
    eal_pct: list[SchoolTrendPointResponse]


class SchoolTrendsHistoryQualityResponse(BaseModel):
    is_partial_history: bool
    min_years_for_delta: int
    years_count: int


class SchoolTrendsCompletenessResponse(BaseModel):
    status: Literal["available", "partial", "unavailable"]
    reason_code: (
        Literal[
            "source_missing",
            "insufficient_years_published",
            "source_not_in_catalog",
            "source_file_missing_for_year",
            "source_schema_incompatible_for_year",
            "partial_metric_coverage",
            "source_not_provided",
            "rejected_by_validation",
            "not_joined_yet",
            "pipeline_failed_recently",
            "not_applicable",
        ]
        | None
    )
    last_updated_at: datetime | None
    years_available: list[str] | None = None


class SchoolTrendsResponse(BaseModel):
    urn: str
    years_available: list[str]
    history_quality: SchoolTrendsHistoryQualityResponse
    series: SchoolTrendsSeriesResponse
    completeness: SchoolTrendsCompletenessResponse
