from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any, Literal, cast

from civitas.application.school_trends.dto import (
    SchoolTrendBenchmarkPointDto,
    SchoolTrendDashboardMetricDto,
    SchoolTrendDashboardResponseDto,
    SchoolTrendDashboardSectionDto,
    SchoolTrendPointDto,
    SchoolTrendsBenchmarksDto,
    SchoolTrendsCompletenessDto,
    SchoolTrendsHistoryQualityDto,
    SchoolTrendsResponseDto,
    SchoolTrendsSectionCompletenessDto,
    SchoolTrendsSeriesDto,
    TrendCompletenessReasonCode,
    TrendDirection,
)
from civitas.application.school_trends.errors import SchoolTrendsNotFoundError
from civitas.application.school_trends.ports.school_benchmark_materializer import (
    SchoolBenchmarkMaterializer,
)
from civitas.application.school_trends.ports.school_trends_repository import (
    SchoolTrendsRepository,
)
from civitas.domain.school_trends.models import (
    SchoolAttendanceYearlyRow,
    SchoolBehaviourYearlyRow,
    SchoolDemographicsYearlyRow,
    SchoolMetricBenchmarkYearlyRow,
    SchoolWorkforceYearlyRow,
)

MIN_YEARS_FOR_DELTA = 2
MIN_YEARS_FOR_COMPLETE_HISTORY = 3
DashboardSectionKey = Literal[
    "demographics",
    "attendance",
    "behaviour",
    "workforce",
    "performance",
    "area",
]

DASHBOARD_SECTION_ORDER = (
    "demographics",
    "attendance",
    "behaviour",
    "workforce",
    "performance",
    "area",
)

DASHBOARD_METRIC_CATALOG: tuple[tuple[str, str, str, str], ...] = (
    ("demographics", "disadvantaged_pct", "Disadvantaged Pupils (%)", "percent"),
    ("demographics", "fsm_pct", "Free School Meals (%)", "percent"),
    ("demographics", "fsm6_pct", "FSM6 (%)", "percent"),
    ("demographics", "sen_pct", "SEN (%)", "percent"),
    ("demographics", "ehcp_pct", "EHCP (%)", "percent"),
    ("demographics", "eal_pct", "EAL (%)", "percent"),
    ("demographics", "male_pct", "Male Pupils (%)", "percent"),
    ("demographics", "female_pct", "Female Pupils (%)", "percent"),
    ("demographics", "pupil_mobility_pct", "Pupil Mobility (%)", "percent"),
    ("attendance", "overall_attendance_pct", "Overall Attendance (%)", "percent"),
    ("attendance", "overall_absence_pct", "Overall Absence (%)", "percent"),
    ("attendance", "persistent_absence_pct", "Persistent Absence (%)", "percent"),
    ("behaviour", "suspensions_count", "Suspensions (count)", "count"),
    ("behaviour", "suspensions_rate", "Suspensions Rate", "rate"),
    (
        "behaviour",
        "permanent_exclusions_count",
        "Permanent Exclusions (count)",
        "count",
    ),
    (
        "behaviour",
        "permanent_exclusions_rate",
        "Permanent Exclusions Rate",
        "rate",
    ),
    ("workforce", "pupil_teacher_ratio", "Pupil to Teacher Ratio", "ratio"),
    ("workforce", "supply_staff_pct", "Supply Staff (%)", "percent"),
    (
        "workforce",
        "teachers_3plus_years_pct",
        "Teachers 3+ Years Experience (%)",
        "percent",
    ),
    ("workforce", "teacher_turnover_pct", "Teacher Turnover (%)", "percent"),
    ("workforce", "qts_pct", "Qualified Teacher Status (%)", "percent"),
    (
        "workforce",
        "qualifications_level6_plus_pct",
        "Level 6+ Qualifications (%)",
        "percent",
    ),
    ("performance", "attainment8_average", "Attainment 8", "score"),
    ("performance", "progress8_average", "Progress 8", "score"),
    (
        "performance",
        "progress8_disadvantaged_gap",
        "Progress 8 Disadvantaged Gap",
        "score",
    ),
    ("performance", "engmath_5_plus_pct", "English & Maths Grade 5+ (%)", "percent"),
    ("performance", "ebacc_entry_pct", "EBacc Entry (%)", "percent"),
    ("area", "area_crime_incidents_per_1000", "Crime Incidents per 1,000", "rate"),
    ("area", "area_house_price_average", "Average House Price", "currency"),
    (
        "area",
        "area_house_price_annual_change_pct",
        "House Price Annual Change (%)",
        "percent",
    ),
)


class GetSchoolTrendsUseCase:
    def __init__(self, school_trends_repository: SchoolTrendsRepository) -> None:
        self._school_trends_repository = school_trends_repository

    def execute(self, *, urn: str) -> SchoolTrendsResponseDto:
        normalized_urn = urn.strip()
        demographics_series = self._school_trends_repository.get_demographics_series(normalized_urn)
        if demographics_series is None:
            raise SchoolTrendsNotFoundError(normalized_urn)

        attendance_series = self._school_trends_repository.get_attendance_series(normalized_urn)
        behaviour_series = self._school_trends_repository.get_behaviour_series(normalized_urn)
        workforce_series = self._school_trends_repository.get_workforce_series(normalized_urn)
        benchmark_series = self._school_trends_repository.get_metric_benchmark_series(
            normalized_urn
        )
        if (
            attendance_series is None
            or behaviour_series is None
            or workforce_series is None
            or benchmark_series is None
        ):
            raise SchoolTrendsNotFoundError(normalized_urn)

        demographics_rows = demographics_series.rows
        attendance_rows = attendance_series.rows
        behaviour_rows = behaviour_series.rows
        workforce_rows = workforce_series.rows

        years_available = _merge_years_available(
            demographics_rows=demographics_rows,
            attendance_rows=attendance_rows,
            behaviour_rows=behaviour_rows,
            workforce_rows=workforce_rows,
        )
        years_count = len(years_available)

        demographics_completeness = _build_completeness(
            years_count=len(tuple(row.academic_year for row in demographics_rows)),
            years_available=tuple(row.academic_year for row in demographics_rows),
            last_updated_at=demographics_series.latest_updated_at,
            has_partial_metric_coverage=_has_partial_metric_coverage_demographics(
                demographics_rows
            ),
        )
        attendance_completeness = _build_completeness(
            years_count=len(tuple(row.academic_year for row in attendance_rows)),
            years_available=tuple(row.academic_year for row in attendance_rows),
            last_updated_at=attendance_series.latest_updated_at,
            has_partial_metric_coverage=_has_partial_metric_coverage_attendance(attendance_rows),
        )
        behaviour_completeness = _build_completeness(
            years_count=len(tuple(row.academic_year for row in behaviour_rows)),
            years_available=tuple(row.academic_year for row in behaviour_rows),
            last_updated_at=behaviour_series.latest_updated_at,
            has_partial_metric_coverage=_has_partial_metric_coverage_behaviour(behaviour_rows),
        )
        workforce_completeness = _build_completeness(
            years_count=len(tuple(row.academic_year for row in workforce_rows)),
            years_available=tuple(row.academic_year for row in workforce_rows),
            last_updated_at=workforce_series.latest_updated_at,
            has_partial_metric_coverage=_has_partial_metric_coverage_workforce(workforce_rows),
        )
        benchmark_rows_by_metric = _group_benchmark_rows_by_metric(benchmark_series.rows)

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
                    rows=demographics_rows,
                    metric_value=lambda row: row.disadvantaged_pct,
                ),
                fsm_pct=_build_metric_series(
                    rows=demographics_rows,
                    metric_value=lambda row: row.fsm_pct,
                ),
                fsm6_pct=_build_metric_series(
                    rows=demographics_rows,
                    metric_value=lambda row: row.fsm6_pct,
                ),
                sen_pct=_build_metric_series(
                    rows=demographics_rows,
                    metric_value=lambda row: row.sen_pct,
                ),
                ehcp_pct=_build_metric_series(
                    rows=demographics_rows,
                    metric_value=lambda row: row.ehcp_pct,
                ),
                eal_pct=_build_metric_series(
                    rows=demographics_rows,
                    metric_value=lambda row: row.eal_pct,
                ),
                first_language_english_pct=_build_metric_series(
                    rows=demographics_rows,
                    metric_value=lambda row: row.first_language_english_pct,
                ),
                first_language_unclassified_pct=_build_metric_series(
                    rows=demographics_rows,
                    metric_value=lambda row: row.first_language_unclassified_pct,
                ),
                male_pct=_build_metric_series(
                    rows=demographics_rows,
                    metric_value=lambda row: row.male_pct,
                ),
                female_pct=_build_metric_series(
                    rows=demographics_rows,
                    metric_value=lambda row: row.female_pct,
                ),
                pupil_mobility_pct=_build_metric_series(
                    rows=demographics_rows,
                    metric_value=lambda row: row.pupil_mobility_pct,
                ),
                overall_attendance_pct=_build_metric_series(
                    rows=attendance_rows,
                    metric_value=lambda row: row.overall_attendance_pct,
                ),
                overall_absence_pct=_build_metric_series(
                    rows=attendance_rows,
                    metric_value=lambda row: row.overall_absence_pct,
                ),
                persistent_absence_pct=_build_metric_series(
                    rows=attendance_rows,
                    metric_value=lambda row: row.persistent_absence_pct,
                ),
                suspensions_count=_build_metric_series(
                    rows=behaviour_rows,
                    metric_value=lambda row: row.suspensions_count,
                ),
                suspensions_rate=_build_metric_series(
                    rows=behaviour_rows,
                    metric_value=lambda row: row.suspensions_rate,
                ),
                permanent_exclusions_count=_build_metric_series(
                    rows=behaviour_rows,
                    metric_value=lambda row: row.permanent_exclusions_count,
                ),
                permanent_exclusions_rate=_build_metric_series(
                    rows=behaviour_rows,
                    metric_value=lambda row: row.permanent_exclusions_rate,
                ),
                pupil_teacher_ratio=_build_metric_series(
                    rows=workforce_rows,
                    metric_value=lambda row: row.pupil_teacher_ratio,
                ),
                supply_staff_pct=_build_metric_series(
                    rows=workforce_rows,
                    metric_value=lambda row: row.supply_staff_pct,
                ),
                teachers_3plus_years_pct=_build_metric_series(
                    rows=workforce_rows,
                    metric_value=lambda row: row.teachers_3plus_years_pct,
                ),
                teacher_turnover_pct=_build_metric_series(
                    rows=workforce_rows,
                    metric_value=lambda row: row.teacher_turnover_pct,
                ),
                qts_pct=_build_metric_series(
                    rows=workforce_rows,
                    metric_value=lambda row: row.qts_pct,
                ),
                qualifications_level6_plus_pct=_build_metric_series(
                    rows=workforce_rows,
                    metric_value=lambda row: row.qualifications_level6_plus_pct,
                ),
            ),
            benchmarks=SchoolTrendsBenchmarksDto(
                disadvantaged_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="disadvantaged_pct",
                ),
                fsm_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="fsm_pct",
                ),
                fsm6_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="fsm6_pct",
                ),
                sen_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="sen_pct",
                ),
                ehcp_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="ehcp_pct",
                ),
                eal_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="eal_pct",
                ),
                first_language_english_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="first_language_english_pct",
                ),
                first_language_unclassified_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="first_language_unclassified_pct",
                ),
                male_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="male_pct",
                ),
                female_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="female_pct",
                ),
                pupil_mobility_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="pupil_mobility_pct",
                ),
                overall_attendance_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="overall_attendance_pct",
                ),
                overall_absence_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="overall_absence_pct",
                ),
                persistent_absence_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="persistent_absence_pct",
                ),
                suspensions_count=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="suspensions_count",
                ),
                suspensions_rate=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="suspensions_rate",
                ),
                permanent_exclusions_count=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="permanent_exclusions_count",
                ),
                permanent_exclusions_rate=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="permanent_exclusions_rate",
                ),
                pupil_teacher_ratio=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="pupil_teacher_ratio",
                ),
                supply_staff_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="supply_staff_pct",
                ),
                teachers_3plus_years_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="teachers_3plus_years_pct",
                ),
                teacher_turnover_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="teacher_turnover_pct",
                ),
                qts_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="qts_pct",
                ),
                qualifications_level6_plus_pct=_build_metric_benchmark_series(
                    rows_by_metric=benchmark_rows_by_metric,
                    metric_key="qualifications_level6_plus_pct",
                ),
            ),
            completeness=_build_overall_completeness(
                years_available=years_available,
                demographics=demographics_completeness,
                attendance=attendance_completeness,
                behaviour=behaviour_completeness,
                workforce=workforce_completeness,
            ),
            section_completeness=SchoolTrendsSectionCompletenessDto(
                demographics=demographics_completeness,
                attendance=attendance_completeness,
                behaviour=behaviour_completeness,
                workforce=workforce_completeness,
            ),
        )


class GetSchoolTrendDashboardUseCase:
    def __init__(self, school_trends_repository: SchoolTrendsRepository) -> None:
        self._school_trends_repository = school_trends_repository

    def execute(self, *, urn: str) -> SchoolTrendDashboardResponseDto:
        normalized_urn = urn.strip()
        trends = GetSchoolTrendsUseCase(
            school_trends_repository=self._school_trends_repository
        ).execute(urn=normalized_urn)

        benchmark_series = self._school_trends_repository.get_metric_benchmark_series(
            normalized_urn
        )
        if benchmark_series is None:
            raise SchoolTrendsNotFoundError(normalized_urn)

        rows_by_metric = _group_benchmark_rows_by_metric(benchmark_series.rows)
        metrics_by_section: dict[str, list[SchoolTrendDashboardMetricDto]] = {
            section: [] for section in DASHBOARD_SECTION_ORDER
        }

        for section, metric_key, label, unit in DASHBOARD_METRIC_CATALOG:
            points = _build_metric_benchmark_series(
                rows_by_metric=rows_by_metric,
                metric_key=metric_key,
            )
            if len(points) == 0:
                continue
            metrics_by_section[section].append(
                SchoolTrendDashboardMetricDto(
                    metric_key=metric_key,
                    label=label,
                    unit=unit,
                    points=points,
                )
            )

        return SchoolTrendDashboardResponseDto(
            urn=trends.urn,
            years_available=_merge_benchmark_years(benchmark_series.rows),
            sections=tuple(
                SchoolTrendDashboardSectionDto(
                    key=cast(DashboardSectionKey, section),
                    metrics=tuple(metrics_by_section[section]),
                )
                for section in DASHBOARD_SECTION_ORDER
            ),
            completeness=trends.completeness,
        )


class MaterializeSchoolBenchmarksUseCase:
    def __init__(self, school_benchmark_materializer: SchoolBenchmarkMaterializer) -> None:
        self._school_benchmark_materializer = school_benchmark_materializer

    def execute(self, *, urns: Sequence[str] | None = None) -> int:
        normalized_urns = tuple(
            dict.fromkeys(urn.strip() for urn in (urns or ()) if urn is not None and urn.strip())
        )
        if len(normalized_urns) == 0:
            return self._school_benchmark_materializer.materialize_all_metric_benchmarks()
        return self._school_benchmark_materializer.materialize_metric_benchmarks_for_urns(
            normalized_urns
        )


def _build_metric_series(
    *,
    rows: Sequence[Any],
    metric_value: Callable[[Any], float | int | None],
) -> tuple[SchoolTrendPointDto, ...]:
    points: list[SchoolTrendPointDto] = []

    for index, row in enumerate(rows):
        value = metric_value(row)
        delta: float | None = None
        direction: TrendDirection | None = None

        if index > 0 and value is not None:
            previous_value = metric_value(rows[index - 1])
            if previous_value is not None:
                delta = float(value) - float(previous_value)
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


def _build_metric_benchmark_series(
    *,
    rows_by_metric: dict[str, tuple[SchoolMetricBenchmarkYearlyRow, ...]],
    metric_key: str,
) -> tuple[SchoolTrendBenchmarkPointDto, ...]:
    rows = rows_by_metric.get(metric_key, ())
    return tuple(
        SchoolTrendBenchmarkPointDto(
            academic_year=row.academic_year,
            school_value=row.school_value,
            national_value=row.national_value,
            local_value=row.local_value,
            school_vs_national_delta=_to_optional_delta(row.school_value, row.national_value),
            school_vs_local_delta=_to_optional_delta(row.school_value, row.local_value),
            local_scope=row.local_scope,
            local_area_code=row.local_area_code,
            local_area_label=row.local_area_label,
        )
        for row in rows
    )


def _group_benchmark_rows_by_metric(
    rows: tuple[SchoolMetricBenchmarkYearlyRow, ...],
) -> dict[str, tuple[SchoolMetricBenchmarkYearlyRow, ...]]:
    grouped: dict[str, list[SchoolMetricBenchmarkYearlyRow]] = {}
    for row in rows:
        grouped.setdefault(row.metric_key, []).append(row)

    return {
        metric_key: tuple(
            sorted(metric_rows, key=lambda item: _academic_year_sort_key(item.academic_year))
        )
        for metric_key, metric_rows in grouped.items()
    }


def _merge_benchmark_years(rows: tuple[SchoolMetricBenchmarkYearlyRow, ...]) -> tuple[str, ...]:
    years = {row.academic_year for row in rows}
    return tuple(sorted(years, key=_academic_year_sort_key))


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
    has_partial_metric_coverage: bool,
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
    if has_partial_metric_coverage:
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


def _build_overall_completeness(
    *,
    years_available: tuple[str, ...],
    demographics: SchoolTrendsCompletenessDto,
    attendance: SchoolTrendsCompletenessDto,
    behaviour: SchoolTrendsCompletenessDto,
    workforce: SchoolTrendsCompletenessDto,
) -> SchoolTrendsCompletenessDto:
    if len(years_available) == 0:
        return SchoolTrendsCompletenessDto(
            status="unavailable",
            reason_code="source_file_missing_for_year",
            last_updated_at=None,
            years_available=years_available,
        )

    sections = (demographics, attendance, behaviour, workforce)
    if all(section.status == "available" for section in sections):
        return SchoolTrendsCompletenessDto(
            status="available",
            reason_code=None,
            last_updated_at=_max_optional_datetime(
                tuple(section.last_updated_at for section in sections)
            ),
            years_available=years_available,
        )

    fallback_reason_code: TrendCompletenessReasonCode = "partial_metric_coverage"
    reason_code = next(
        (section.reason_code for section in sections if section.reason_code is not None),
        fallback_reason_code,
    )
    return SchoolTrendsCompletenessDto(
        status="partial",
        reason_code=reason_code,
        last_updated_at=_max_optional_datetime(
            tuple(section.last_updated_at for section in sections)
        ),
        years_available=years_available,
    )


def _merge_years_available(
    *,
    demographics_rows: Sequence[SchoolDemographicsYearlyRow],
    attendance_rows: Sequence[SchoolAttendanceYearlyRow],
    behaviour_rows: Sequence[SchoolBehaviourYearlyRow],
    workforce_rows: Sequence[SchoolWorkforceYearlyRow],
) -> tuple[str, ...]:
    years = {
        *(row.academic_year for row in demographics_rows),
        *(row.academic_year for row in attendance_rows),
        *(row.academic_year for row in behaviour_rows),
        *(row.academic_year for row in workforce_rows),
    }
    return tuple(sorted(years, key=_academic_year_sort_key))


def _has_partial_metric_coverage_demographics(rows: Sequence[SchoolDemographicsYearlyRow]) -> bool:
    for row in rows:
        if any(
            value is None
            for value in (
                row.disadvantaged_pct,
                row.fsm_pct,
                row.fsm6_pct,
                row.sen_pct,
                row.ehcp_pct,
                row.eal_pct,
                row.first_language_english_pct,
                row.first_language_unclassified_pct,
                row.male_pct,
                row.female_pct,
                row.pupil_mobility_pct,
            )
        ):
            return True
    return False


def _has_partial_metric_coverage_attendance(rows: Sequence[SchoolAttendanceYearlyRow]) -> bool:
    for row in rows:
        if any(
            value is None
            for value in (
                row.overall_attendance_pct,
                row.overall_absence_pct,
                row.persistent_absence_pct,
            )
        ):
            return True
    return False


def _has_partial_metric_coverage_behaviour(rows: Sequence[SchoolBehaviourYearlyRow]) -> bool:
    for row in rows:
        if any(
            value is None
            for value in (
                row.suspensions_count,
                row.suspensions_rate,
                row.permanent_exclusions_count,
                row.permanent_exclusions_rate,
            )
        ):
            return True
    return False


def _has_partial_metric_coverage_workforce(rows: Sequence[SchoolWorkforceYearlyRow]) -> bool:
    for row in rows:
        if any(
            value is None
            for value in (
                row.pupil_teacher_ratio,
                row.supply_staff_pct,
                row.teachers_3plus_years_pct,
                row.teacher_turnover_pct,
                row.qts_pct,
                row.qualifications_level6_plus_pct,
            )
        ):
            return True
    return False


def _academic_year_sort_key(value: str) -> tuple[int, str]:
    try:
        start_year = int(value.split("/", maxsplit=1)[0])
    except (ValueError, IndexError):
        start_year = -1
    return start_year, value


def _max_optional_datetime(values: tuple[datetime | None, ...]) -> datetime | None:
    non_null_values = [value for value in values if value is not None]
    if not non_null_values:
        return None
    return max(non_null_values)


def _to_optional_delta(school_value: float | None, benchmark_value: float | None) -> float | None:
    if school_value is None or benchmark_value is None:
        return None
    return float(school_value) - float(benchmark_value)
