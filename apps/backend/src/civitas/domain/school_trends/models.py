from dataclasses import dataclass
from datetime import datetime
from typing import Literal

TrendCompletenessStatus = Literal["available", "partial", "unavailable"]
BenchmarkScope = Literal["local_authority_district", "phase"]
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
]


@dataclass(frozen=True)
class SchoolDemographicsYearlyRow:
    academic_year: str
    disadvantaged_pct: float | None
    fsm_pct: float | None
    fsm6_pct: float | None
    sen_pct: float | None
    ehcp_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None
    male_pct: float | None
    female_pct: float | None
    pupil_mobility_pct: float | None


@dataclass(frozen=True)
class SchoolDemographicsSeries:
    urn: str
    rows: tuple[SchoolDemographicsYearlyRow, ...]
    latest_updated_at: datetime | None


@dataclass(frozen=True)
class SchoolAttendanceYearlyRow:
    academic_year: str
    overall_attendance_pct: float | None
    overall_absence_pct: float | None
    persistent_absence_pct: float | None


@dataclass(frozen=True)
class SchoolAttendanceSeries:
    urn: str
    rows: tuple[SchoolAttendanceYearlyRow, ...]
    latest_updated_at: datetime | None


@dataclass(frozen=True)
class SchoolBehaviourYearlyRow:
    academic_year: str
    suspensions_count: int | None
    suspensions_rate: float | None
    permanent_exclusions_count: int | None
    permanent_exclusions_rate: float | None


@dataclass(frozen=True)
class SchoolBehaviourSeries:
    urn: str
    rows: tuple[SchoolBehaviourYearlyRow, ...]
    latest_updated_at: datetime | None


@dataclass(frozen=True)
class SchoolWorkforceYearlyRow:
    academic_year: str
    pupil_teacher_ratio: float | None
    supply_staff_pct: float | None
    teachers_3plus_years_pct: float | None
    teacher_turnover_pct: float | None
    qts_pct: float | None
    qualifications_level6_plus_pct: float | None


@dataclass(frozen=True)
class SchoolFinanceYearlyRow:
    academic_year: str
    total_income_gbp: float | None
    total_expenditure_gbp: float | None
    income_per_pupil_gbp: float | None
    expenditure_per_pupil_gbp: float | None
    total_staff_costs_gbp: float | None
    staff_costs_pct_of_expenditure: float | None
    teaching_staff_costs_per_pupil_gbp: float | None
    revenue_reserve_gbp: float | None
    revenue_reserve_per_pupil_gbp: float | None


@dataclass(frozen=True)
class SchoolWorkforceSeries:
    urn: str
    rows: tuple[SchoolWorkforceYearlyRow, ...]
    latest_updated_at: datetime | None


@dataclass(frozen=True)
class SchoolFinanceSeries:
    urn: str
    rows: tuple[SchoolFinanceYearlyRow, ...]
    latest_updated_at: datetime | None
    is_applicable: bool


@dataclass(frozen=True)
class SchoolMetricBenchmarkYearlyRow:
    metric_key: str
    academic_year: str
    school_value: float | None
    national_value: float | None
    local_value: float | None
    local_scope: BenchmarkScope
    local_area_code: str
    local_area_label: str


@dataclass(frozen=True)
class SchoolMetricBenchmarkSeries:
    urn: str
    rows: tuple[SchoolMetricBenchmarkYearlyRow, ...]
    latest_updated_at: datetime | None
