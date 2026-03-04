from collections.abc import Callable, Sequence
from datetime import datetime

from civitas.application.school_trends.dto import (
    SchoolTrendPointDto,
    SchoolTrendsCompletenessDto,
    SchoolTrendsHistoryQualityDto,
    SchoolTrendsResponseDto,
    SchoolTrendsSeriesDto,
    TrendDirection,
)
from civitas.application.school_trends.errors import SchoolTrendsNotFoundError
from civitas.application.school_trends.ports.school_trends_repository import (
    SchoolTrendsRepository,
)
from civitas.domain.school_trends.models import SchoolDemographicsYearlyRow

MIN_YEARS_FOR_DELTA = 2
MIN_YEARS_FOR_COMPLETE_HISTORY = 3


class GetSchoolTrendsUseCase:
    def __init__(self, school_trends_repository: SchoolTrendsRepository) -> None:
        self._school_trends_repository = school_trends_repository

    def execute(self, *, urn: str) -> SchoolTrendsResponseDto:
        normalized_urn = urn.strip()
        demographics_series = self._school_trends_repository.get_demographics_series(normalized_urn)
        if demographics_series is None:
            raise SchoolTrendsNotFoundError(normalized_urn)

        rows = demographics_series.rows
        years_available = tuple(row.academic_year for row in rows)
        years_count = len(years_available)
        completeness = _build_completeness(
            years_count=years_count,
            years_available=years_available,
            last_updated_at=demographics_series.latest_updated_at,
            rows=rows,
        )

        return SchoolTrendsResponseDto(
            urn=demographics_series.urn,
            years_available=years_available,
            history_quality=SchoolTrendsHistoryQualityDto(
                is_partial_history=years_count < MIN_YEARS_FOR_COMPLETE_HISTORY,
                min_years_for_delta=MIN_YEARS_FOR_DELTA,
                years_count=years_count,
            ),
            series=SchoolTrendsSeriesDto(
                disadvantaged_pct=_build_metric_series(
                    rows=rows,
                    metric_value=lambda row: row.disadvantaged_pct,
                ),
                sen_pct=_build_metric_series(
                    rows=rows,
                    metric_value=lambda row: row.sen_pct,
                ),
                ehcp_pct=_build_metric_series(
                    rows=rows,
                    metric_value=lambda row: row.ehcp_pct,
                ),
                eal_pct=_build_metric_series(
                    rows=rows,
                    metric_value=lambda row: row.eal_pct,
                ),
                first_language_english_pct=_build_metric_series(
                    rows=rows,
                    metric_value=lambda row: row.first_language_english_pct,
                ),
                first_language_unclassified_pct=_build_metric_series(
                    rows=rows,
                    metric_value=lambda row: row.first_language_unclassified_pct,
                ),
            ),
            completeness=completeness,
        )


def _build_metric_series(
    *,
    rows: Sequence[SchoolDemographicsYearlyRow],
    metric_value: Callable[[SchoolDemographicsYearlyRow], float | None],
) -> tuple[SchoolTrendPointDto, ...]:
    points: list[SchoolTrendPointDto] = []

    for index, row in enumerate(rows):
        value = metric_value(row)
        delta: float | None = None
        direction: TrendDirection | None = None

        if index > 0 and value is not None:
            previous_value = metric_value(rows[index - 1])
            if previous_value is not None:
                delta = value - previous_value
                direction = _direction_from_delta(delta)

        points.append(
            SchoolTrendPointDto(
                academic_year=row.academic_year,
                value=value,
                delta=delta,
                direction=direction,
            )
        )

    return tuple(points)


def _direction_from_delta(delta: float) -> TrendDirection:
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "flat"


def _build_completeness(
    *,
    years_count: int,
    years_available: tuple[str, ...],
    last_updated_at: datetime | None,
    rows: Sequence[SchoolDemographicsYearlyRow],
) -> SchoolTrendsCompletenessDto:
    if years_count == 0:
        return SchoolTrendsCompletenessDto(
            status="unavailable",
            reason_code="source_file_missing_for_year",
            last_updated_at=None,
            years_available=years_available,
        )
    if years_count < MIN_YEARS_FOR_COMPLETE_HISTORY:
        return SchoolTrendsCompletenessDto(
            status="partial",
            reason_code="insufficient_years_published",
            last_updated_at=last_updated_at,
            years_available=years_available,
        )
    if _has_partial_metric_coverage(rows):
        return SchoolTrendsCompletenessDto(
            status="partial",
            reason_code="partial_metric_coverage",
            last_updated_at=last_updated_at,
            years_available=years_available,
        )
    return SchoolTrendsCompletenessDto(
        status="available",
        reason_code=None,
        last_updated_at=last_updated_at,
        years_available=years_available,
    )


def _has_partial_metric_coverage(rows: Sequence[SchoolDemographicsYearlyRow]) -> bool:
    for row in rows:
        if any(
            value is None
            for value in (
                row.disadvantaged_pct,
                row.sen_pct,
                row.ehcp_pct,
                row.eal_pct,
                row.first_language_english_pct,
                row.first_language_unclassified_pct,
            )
        ):
            return True
    return False
