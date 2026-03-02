from dataclasses import dataclass
from typing import Literal

TrendDirection = Literal["up", "down", "flat"]


@dataclass(frozen=True)
class SchoolTrendPointDto:
    academic_year: str
    value: float | None
    delta: float | None
    direction: TrendDirection | None


@dataclass(frozen=True)
class SchoolTrendsHistoryQualityDto:
    is_partial_history: bool
    min_years_for_delta: int
    years_count: int


@dataclass(frozen=True)
class SchoolTrendsSeriesDto:
    disadvantaged_pct: tuple[SchoolTrendPointDto, ...]
    sen_pct: tuple[SchoolTrendPointDto, ...]
    ehcp_pct: tuple[SchoolTrendPointDto, ...]
    eal_pct: tuple[SchoolTrendPointDto, ...]


@dataclass(frozen=True)
class SchoolTrendsResponseDto:
    urn: str
    years_available: tuple[str, ...]
    history_quality: SchoolTrendsHistoryQualityDto
    series: SchoolTrendsSeriesDto
