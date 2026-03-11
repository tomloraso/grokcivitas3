from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from civitas.api.schemas.subject_performance import SchoolSubjectPerformanceSeriesResponse

BenchmarkScope = Literal["local_authority_district", "phase"]


class SchoolTrendPointResponse(BaseModel):
    academic_year: str
    value: float | int | None
    delta: float | None
    direction: Literal["up", "down", "flat"] | None


class SchoolTrendBenchmarkPointResponse(BaseModel):
    academic_year: str
    school_value: float | int | None
    national_value: float | None
    local_value: float | None
    school_vs_national_delta: float | None
    school_vs_local_delta: float | None
    local_scope: BenchmarkScope
    local_area_code: str
    local_area_label: str


class SchoolTrendsSeriesResponse(BaseModel):
    disadvantaged_pct: list[SchoolTrendPointResponse]
    fsm_pct: list[SchoolTrendPointResponse]
    fsm6_pct: list[SchoolTrendPointResponse]
    sen_pct: list[SchoolTrendPointResponse]
    ehcp_pct: list[SchoolTrendPointResponse]
    eal_pct: list[SchoolTrendPointResponse]
    first_language_english_pct: list[SchoolTrendPointResponse]
    first_language_unclassified_pct: list[SchoolTrendPointResponse]
    male_pct: list[SchoolTrendPointResponse]
    female_pct: list[SchoolTrendPointResponse]
    pupil_mobility_pct: list[SchoolTrendPointResponse]
    overall_attendance_pct: list[SchoolTrendPointResponse]
    overall_absence_pct: list[SchoolTrendPointResponse]
    persistent_absence_pct: list[SchoolTrendPointResponse]
    suspensions_count: list[SchoolTrendPointResponse]
    suspensions_rate: list[SchoolTrendPointResponse]
    permanent_exclusions_count: list[SchoolTrendPointResponse]
    permanent_exclusions_rate: list[SchoolTrendPointResponse]
    pupil_teacher_ratio: list[SchoolTrendPointResponse]
    supply_staff_pct: list[SchoolTrendPointResponse]
    teachers_3plus_years_pct: list[SchoolTrendPointResponse]
    teacher_turnover_pct: list[SchoolTrendPointResponse]
    qts_pct: list[SchoolTrendPointResponse]
    qualifications_level6_plus_pct: list[SchoolTrendPointResponse]
    teacher_headcount_total: list[SchoolTrendPointResponse]
    teacher_fte_total: list[SchoolTrendPointResponse]
    support_staff_headcount_total: list[SchoolTrendPointResponse]
    support_staff_fte_total: list[SchoolTrendPointResponse]
    leadership_share_of_teachers: list[SchoolTrendPointResponse]
    teacher_average_mean_salary_gbp: list[SchoolTrendPointResponse]
    teacher_average_median_salary_gbp: list[SchoolTrendPointResponse]
    teachers_on_leadership_pay_range_pct: list[SchoolTrendPointResponse]
    teacher_absence_pct: list[SchoolTrendPointResponse]
    teacher_absence_days_total: list[SchoolTrendPointResponse]
    teacher_absence_days_average: list[SchoolTrendPointResponse]
    teacher_absence_days_average_all_teachers: list[SchoolTrendPointResponse]
    teacher_vacancy_count: list[SchoolTrendPointResponse]
    teacher_vacancy_rate: list[SchoolTrendPointResponse]
    teacher_tempfilled_vacancy_count: list[SchoolTrendPointResponse]
    teacher_tempfilled_vacancy_rate: list[SchoolTrendPointResponse]
    third_party_support_staff_headcount: list[SchoolTrendPointResponse]
    ks4_overall_pct: list[SchoolTrendPointResponse]
    ks4_education_pct: list[SchoolTrendPointResponse]
    ks4_apprenticeship_pct: list[SchoolTrendPointResponse]
    ks4_employment_pct: list[SchoolTrendPointResponse]
    ks4_not_sustained_pct: list[SchoolTrendPointResponse]
    ks4_activity_unknown_pct: list[SchoolTrendPointResponse]
    study_16_18_overall_pct: list[SchoolTrendPointResponse]
    study_16_18_education_pct: list[SchoolTrendPointResponse]
    study_16_18_apprenticeship_pct: list[SchoolTrendPointResponse]
    study_16_18_employment_pct: list[SchoolTrendPointResponse]
    study_16_18_not_sustained_pct: list[SchoolTrendPointResponse]
    study_16_18_activity_unknown_pct: list[SchoolTrendPointResponse]
    admissions_oversubscription_ratio: list[SchoolTrendPointResponse]
    admissions_first_preference_offer_rate: list[SchoolTrendPointResponse]
    admissions_any_preference_offer_rate: list[SchoolTrendPointResponse]
    admissions_cross_la_applications: list[SchoolTrendPointResponse]
    admissions_cross_la_offers: list[SchoolTrendPointResponse]
    income_per_pupil_gbp: list[SchoolTrendPointResponse]
    expenditure_per_pupil_gbp: list[SchoolTrendPointResponse]
    staff_costs_pct_of_expenditure: list[SchoolTrendPointResponse]
    revenue_reserve_per_pupil_gbp: list[SchoolTrendPointResponse]
    teaching_staff_costs_per_pupil_gbp: list[SchoolTrendPointResponse]
    supply_staff_costs_pct_of_staff_costs: list[SchoolTrendPointResponse]


class SchoolTrendsBenchmarksResponse(BaseModel):
    disadvantaged_pct: list[SchoolTrendBenchmarkPointResponse]
    fsm_pct: list[SchoolTrendBenchmarkPointResponse]
    fsm6_pct: list[SchoolTrendBenchmarkPointResponse]
    sen_pct: list[SchoolTrendBenchmarkPointResponse]
    ehcp_pct: list[SchoolTrendBenchmarkPointResponse]
    eal_pct: list[SchoolTrendBenchmarkPointResponse]
    first_language_english_pct: list[SchoolTrendBenchmarkPointResponse]
    first_language_unclassified_pct: list[SchoolTrendBenchmarkPointResponse]
    male_pct: list[SchoolTrendBenchmarkPointResponse]
    female_pct: list[SchoolTrendBenchmarkPointResponse]
    pupil_mobility_pct: list[SchoolTrendBenchmarkPointResponse]
    overall_attendance_pct: list[SchoolTrendBenchmarkPointResponse]
    overall_absence_pct: list[SchoolTrendBenchmarkPointResponse]
    persistent_absence_pct: list[SchoolTrendBenchmarkPointResponse]
    suspensions_count: list[SchoolTrendBenchmarkPointResponse]
    suspensions_rate: list[SchoolTrendBenchmarkPointResponse]
    permanent_exclusions_count: list[SchoolTrendBenchmarkPointResponse]
    permanent_exclusions_rate: list[SchoolTrendBenchmarkPointResponse]
    pupil_teacher_ratio: list[SchoolTrendBenchmarkPointResponse]
    supply_staff_pct: list[SchoolTrendBenchmarkPointResponse]
    teachers_3plus_years_pct: list[SchoolTrendBenchmarkPointResponse]
    teacher_turnover_pct: list[SchoolTrendBenchmarkPointResponse]
    qts_pct: list[SchoolTrendBenchmarkPointResponse]
    qualifications_level6_plus_pct: list[SchoolTrendBenchmarkPointResponse]
    teacher_headcount_total: list[SchoolTrendBenchmarkPointResponse]
    teacher_fte_total: list[SchoolTrendBenchmarkPointResponse]
    support_staff_headcount_total: list[SchoolTrendBenchmarkPointResponse]
    support_staff_fte_total: list[SchoolTrendBenchmarkPointResponse]
    leadership_share_of_teachers: list[SchoolTrendBenchmarkPointResponse]
    teacher_average_mean_salary_gbp: list[SchoolTrendBenchmarkPointResponse]
    teacher_average_median_salary_gbp: list[SchoolTrendBenchmarkPointResponse]
    teachers_on_leadership_pay_range_pct: list[SchoolTrendBenchmarkPointResponse]
    teacher_absence_pct: list[SchoolTrendBenchmarkPointResponse]
    teacher_absence_days_total: list[SchoolTrendBenchmarkPointResponse]
    teacher_absence_days_average: list[SchoolTrendBenchmarkPointResponse]
    teacher_absence_days_average_all_teachers: list[SchoolTrendBenchmarkPointResponse]
    teacher_vacancy_count: list[SchoolTrendBenchmarkPointResponse]
    teacher_vacancy_rate: list[SchoolTrendBenchmarkPointResponse]
    teacher_tempfilled_vacancy_count: list[SchoolTrendBenchmarkPointResponse]
    teacher_tempfilled_vacancy_rate: list[SchoolTrendBenchmarkPointResponse]
    third_party_support_staff_headcount: list[SchoolTrendBenchmarkPointResponse]
    admissions_oversubscription_ratio: list[SchoolTrendBenchmarkPointResponse]
    admissions_first_preference_offer_rate: list[SchoolTrendBenchmarkPointResponse]
    admissions_any_preference_offer_rate: list[SchoolTrendBenchmarkPointResponse]
    admissions_cross_la_applications: list[SchoolTrendBenchmarkPointResponse]
    income_per_pupil_gbp: list[SchoolTrendBenchmarkPointResponse]
    expenditure_per_pupil_gbp: list[SchoolTrendBenchmarkPointResponse]
    staff_costs_pct_of_expenditure: list[SchoolTrendBenchmarkPointResponse]
    revenue_reserve_per_pupil_gbp: list[SchoolTrendBenchmarkPointResponse]
    teaching_staff_costs_per_pupil_gbp: list[SchoolTrendBenchmarkPointResponse]
    supply_staff_costs_pct_of_staff_costs: list[SchoolTrendBenchmarkPointResponse]


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
            "unsupported_stage",
        ]
        | None
    )
    last_updated_at: datetime | None
    years_available: list[str] | None = None


class SchoolTrendsSectionCompletenessResponse(BaseModel):
    demographics: SchoolTrendsCompletenessResponse
    attendance: SchoolTrendsCompletenessResponse
    behaviour: SchoolTrendsCompletenessResponse
    workforce: SchoolTrendsCompletenessResponse
    admissions: SchoolTrendsCompletenessResponse
    destinations: SchoolTrendsCompletenessResponse
    finance: SchoolTrendsCompletenessResponse


class SchoolTrendsResponse(BaseModel):
    urn: str
    years_available: list[str]
    history_quality: SchoolTrendsHistoryQualityResponse
    series: SchoolTrendsSeriesResponse
    benchmarks: SchoolTrendsBenchmarksResponse
    completeness: SchoolTrendsCompletenessResponse
    section_completeness: SchoolTrendsSectionCompletenessResponse
    subject_performance: SchoolSubjectPerformanceSeriesResponse | None = None


class SchoolTrendDashboardMetricResponse(BaseModel):
    metric_key: str
    label: str
    unit: str
    points: list[SchoolTrendBenchmarkPointResponse]


class SchoolTrendDashboardSectionResponse(BaseModel):
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
    metrics: list[SchoolTrendDashboardMetricResponse]


class SchoolTrendDashboardResponse(BaseModel):
    urn: str
    years_available: list[str]
    sections: list[SchoolTrendDashboardSectionResponse]
    completeness: SchoolTrendsCompletenessResponse
