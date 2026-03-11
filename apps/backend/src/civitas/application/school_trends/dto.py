from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from civitas.application.subject_performance.dto import SchoolSubjectPerformanceSeriesDto

TrendDirection = Literal["up", "down", "flat"]
BenchmarkScope = Literal["local_authority_district", "phase"]
TrendCompletenessStatus = Literal["available", "partial", "unavailable"]
TrendCompletenessReasonCode = Literal[
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
    "unsupported_stage",
]


@dataclass(frozen=True)
class SchoolTrendPointDto:
    academic_year: str
    value: float | int | None
    delta: float | None
    direction: TrendDirection | None


@dataclass(frozen=True)
class SchoolTrendBenchmarkPointDto:
    academic_year: str
    school_value: float | int | None
    national_value: float | None
    local_value: float | None
    school_vs_national_delta: float | None
    school_vs_local_delta: float | None
    local_scope: BenchmarkScope
    local_area_code: str
    local_area_label: str


@dataclass(frozen=True)
class SchoolTrendsHistoryQualityDto:
    is_partial_history: bool
    min_years_for_delta: int
    years_count: int


@dataclass(frozen=True)
class SchoolTrendsSeriesDto:
    disadvantaged_pct: tuple[SchoolTrendPointDto, ...]
    fsm_pct: tuple[SchoolTrendPointDto, ...]
    fsm6_pct: tuple[SchoolTrendPointDto, ...]
    sen_pct: tuple[SchoolTrendPointDto, ...]
    ehcp_pct: tuple[SchoolTrendPointDto, ...]
    eal_pct: tuple[SchoolTrendPointDto, ...]
    first_language_english_pct: tuple[SchoolTrendPointDto, ...]
    first_language_unclassified_pct: tuple[SchoolTrendPointDto, ...]
    male_pct: tuple[SchoolTrendPointDto, ...]
    female_pct: tuple[SchoolTrendPointDto, ...]
    pupil_mobility_pct: tuple[SchoolTrendPointDto, ...]
    overall_attendance_pct: tuple[SchoolTrendPointDto, ...]
    overall_absence_pct: tuple[SchoolTrendPointDto, ...]
    persistent_absence_pct: tuple[SchoolTrendPointDto, ...]
    suspensions_count: tuple[SchoolTrendPointDto, ...]
    suspensions_rate: tuple[SchoolTrendPointDto, ...]
    permanent_exclusions_count: tuple[SchoolTrendPointDto, ...]
    permanent_exclusions_rate: tuple[SchoolTrendPointDto, ...]
    pupil_teacher_ratio: tuple[SchoolTrendPointDto, ...]
    supply_staff_pct: tuple[SchoolTrendPointDto, ...]
    teachers_3plus_years_pct: tuple[SchoolTrendPointDto, ...]
    teacher_turnover_pct: tuple[SchoolTrendPointDto, ...]
    qts_pct: tuple[SchoolTrendPointDto, ...]
    qualifications_level6_plus_pct: tuple[SchoolTrendPointDto, ...]
    income_per_pupil_gbp: tuple[SchoolTrendPointDto, ...]
    expenditure_per_pupil_gbp: tuple[SchoolTrendPointDto, ...]
    staff_costs_pct_of_expenditure: tuple[SchoolTrendPointDto, ...]
    revenue_reserve_per_pupil_gbp: tuple[SchoolTrendPointDto, ...]
    teaching_staff_costs_per_pupil_gbp: tuple[SchoolTrendPointDto, ...]
    supply_staff_costs_pct_of_staff_costs: tuple[SchoolTrendPointDto, ...]
    ks4_overall_pct: tuple[SchoolTrendPointDto, ...] = ()
    ks4_education_pct: tuple[SchoolTrendPointDto, ...] = ()
    ks4_apprenticeship_pct: tuple[SchoolTrendPointDto, ...] = ()
    ks4_employment_pct: tuple[SchoolTrendPointDto, ...] = ()
    ks4_not_sustained_pct: tuple[SchoolTrendPointDto, ...] = ()
    ks4_activity_unknown_pct: tuple[SchoolTrendPointDto, ...] = ()
    study_16_18_overall_pct: tuple[SchoolTrendPointDto, ...] = ()
    study_16_18_education_pct: tuple[SchoolTrendPointDto, ...] = ()
    study_16_18_apprenticeship_pct: tuple[SchoolTrendPointDto, ...] = ()
    study_16_18_employment_pct: tuple[SchoolTrendPointDto, ...] = ()
    study_16_18_not_sustained_pct: tuple[SchoolTrendPointDto, ...] = ()
    study_16_18_activity_unknown_pct: tuple[SchoolTrendPointDto, ...] = ()
    admissions_oversubscription_ratio: tuple[SchoolTrendPointDto, ...] = ()
    admissions_first_preference_offer_rate: tuple[SchoolTrendPointDto, ...] = ()
    admissions_any_preference_offer_rate: tuple[SchoolTrendPointDto, ...] = ()
    admissions_cross_la_applications: tuple[SchoolTrendPointDto, ...] = ()
    admissions_cross_la_offers: tuple[SchoolTrendPointDto, ...] = ()
    teacher_headcount_total: tuple[SchoolTrendPointDto, ...] = ()
    teacher_fte_total: tuple[SchoolTrendPointDto, ...] = ()
    support_staff_headcount_total: tuple[SchoolTrendPointDto, ...] = ()
    support_staff_fte_total: tuple[SchoolTrendPointDto, ...] = ()
    leadership_share_of_teachers: tuple[SchoolTrendPointDto, ...] = ()
    teacher_average_mean_salary_gbp: tuple[SchoolTrendPointDto, ...] = ()
    teacher_average_median_salary_gbp: tuple[SchoolTrendPointDto, ...] = ()
    teachers_on_leadership_pay_range_pct: tuple[SchoolTrendPointDto, ...] = ()
    teacher_absence_pct: tuple[SchoolTrendPointDto, ...] = ()
    teacher_absence_days_total: tuple[SchoolTrendPointDto, ...] = ()
    teacher_absence_days_average: tuple[SchoolTrendPointDto, ...] = ()
    teacher_absence_days_average_all_teachers: tuple[SchoolTrendPointDto, ...] = ()
    teacher_vacancy_count: tuple[SchoolTrendPointDto, ...] = ()
    teacher_vacancy_rate: tuple[SchoolTrendPointDto, ...] = ()
    teacher_tempfilled_vacancy_count: tuple[SchoolTrendPointDto, ...] = ()
    teacher_tempfilled_vacancy_rate: tuple[SchoolTrendPointDto, ...] = ()
    third_party_support_staff_headcount: tuple[SchoolTrendPointDto, ...] = ()


@dataclass(frozen=True)
class SchoolTrendsBenchmarksDto:
    disadvantaged_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    fsm_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    fsm6_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    sen_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    ehcp_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    eal_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    first_language_english_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    first_language_unclassified_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    male_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    female_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    pupil_mobility_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    overall_attendance_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    overall_absence_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    persistent_absence_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    suspensions_count: tuple[SchoolTrendBenchmarkPointDto, ...]
    suspensions_rate: tuple[SchoolTrendBenchmarkPointDto, ...]
    permanent_exclusions_count: tuple[SchoolTrendBenchmarkPointDto, ...]
    permanent_exclusions_rate: tuple[SchoolTrendBenchmarkPointDto, ...]
    pupil_teacher_ratio: tuple[SchoolTrendBenchmarkPointDto, ...]
    supply_staff_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    teachers_3plus_years_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    teacher_turnover_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    qts_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    qualifications_level6_plus_pct: tuple[SchoolTrendBenchmarkPointDto, ...]
    income_per_pupil_gbp: tuple[SchoolTrendBenchmarkPointDto, ...]
    expenditure_per_pupil_gbp: tuple[SchoolTrendBenchmarkPointDto, ...]
    staff_costs_pct_of_expenditure: tuple[SchoolTrendBenchmarkPointDto, ...]
    revenue_reserve_per_pupil_gbp: tuple[SchoolTrendBenchmarkPointDto, ...]
    teaching_staff_costs_per_pupil_gbp: tuple[SchoolTrendBenchmarkPointDto, ...]
    supply_staff_costs_pct_of_staff_costs: tuple[SchoolTrendBenchmarkPointDto, ...]
    admissions_oversubscription_ratio: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    admissions_first_preference_offer_rate: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    admissions_any_preference_offer_rate: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    admissions_cross_la_applications: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_headcount_total: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_fte_total: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    support_staff_headcount_total: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    support_staff_fte_total: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    leadership_share_of_teachers: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_average_mean_salary_gbp: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_average_median_salary_gbp: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teachers_on_leadership_pay_range_pct: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_absence_pct: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_absence_days_total: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_absence_days_average: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_absence_days_average_all_teachers: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_vacancy_count: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_vacancy_rate: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_tempfilled_vacancy_count: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    teacher_tempfilled_vacancy_rate: tuple[SchoolTrendBenchmarkPointDto, ...] = ()
    third_party_support_staff_headcount: tuple[SchoolTrendBenchmarkPointDto, ...] = ()


@dataclass(frozen=True)
class SchoolTrendsCompletenessDto:
    status: TrendCompletenessStatus
    reason_code: TrendCompletenessReasonCode | None
    last_updated_at: datetime | None
    years_available: tuple[str, ...] | None = None


@dataclass(frozen=True)
class SchoolTrendsSectionCompletenessDto:
    demographics: SchoolTrendsCompletenessDto
    attendance: SchoolTrendsCompletenessDto
    behaviour: SchoolTrendsCompletenessDto
    workforce: SchoolTrendsCompletenessDto
    admissions: SchoolTrendsCompletenessDto
    destinations: SchoolTrendsCompletenessDto
    finance: SchoolTrendsCompletenessDto


@dataclass(frozen=True)
class SchoolTrendsResponseDto:
    urn: str
    years_available: tuple[str, ...]
    history_quality: SchoolTrendsHistoryQualityDto
    series: SchoolTrendsSeriesDto
    benchmarks: SchoolTrendsBenchmarksDto
    completeness: SchoolTrendsCompletenessDto
    section_completeness: SchoolTrendsSectionCompletenessDto
    subject_performance: SchoolSubjectPerformanceSeriesDto | None = None


@dataclass(frozen=True)
class SchoolTrendDashboardMetricDto:
    metric_key: str
    label: str
    unit: str
    points: tuple[SchoolTrendBenchmarkPointDto, ...]


@dataclass(frozen=True)
class SchoolTrendDashboardSectionDto:
    key: Literal[
        "demographics",
        "admissions",
        "finance",
        "attendance",
        "behaviour",
        "workforce",
        "performance",
        "area",
    ]
    metrics: tuple[SchoolTrendDashboardMetricDto, ...]


@dataclass(frozen=True)
class SchoolTrendDashboardResponseDto:
    urn: str
    years_available: tuple[str, ...]
    sections: tuple[SchoolTrendDashboardSectionDto, ...]
    completeness: SchoolTrendsCompletenessDto
