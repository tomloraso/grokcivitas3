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


class SchoolTrendsResponse(BaseModel):
    urn: str
    years_available: list[str]
    history_quality: SchoolTrendsHistoryQualityResponse
    series: SchoolTrendsSeriesResponse
