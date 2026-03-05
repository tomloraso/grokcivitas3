from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

SectionCompletenessStatus = Literal["available", "partial", "unavailable"]
SectionCompletenessReasonCode = Literal[
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
    "source_coverage_gap",
    "stale_after_school_refresh",
    "no_incidents_in_radius",
]


@dataclass(frozen=True)
class SchoolProfileSchoolDto:
    urn: str
    name: str
    phase: str | None
    school_type: str | None
    status: str | None
    postcode: str | None
    lat: float
    lng: float


@dataclass(frozen=True)
class SchoolDemographicsCoverageDto:
    fsm_supported: bool
    ethnicity_supported: bool
    top_languages_supported: bool
    fsm6_supported: bool = False
    gender_supported: bool = False
    mobility_supported: bool = False
    send_primary_need_supported: bool = False


@dataclass(frozen=True)
class SchoolDemographicsEthnicityGroupDto:
    key: str
    label: str
    percentage: float | None
    count: int | None


@dataclass(frozen=True)
class SchoolDemographicsSendPrimaryNeedDto:
    key: str
    label: str
    percentage: float | None
    count: int | None


@dataclass(frozen=True)
class SchoolDemographicsHomeLanguageDto:
    key: str
    label: str
    rank: int
    percentage: float | None
    count: int | None


@dataclass(frozen=True)
class SchoolDemographicsLatestDto:
    academic_year: str
    disadvantaged_pct: float | None
    fsm_pct: float | None
    sen_pct: float | None
    ehcp_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None
    coverage: SchoolDemographicsCoverageDto
    fsm6_pct: float | None = None
    male_pct: float | None = None
    female_pct: float | None = None
    pupil_mobility_pct: float | None = None
    ethnicity_breakdown: tuple[SchoolDemographicsEthnicityGroupDto, ...] = ()
    send_primary_needs: tuple[SchoolDemographicsSendPrimaryNeedDto, ...] = ()
    top_home_languages: tuple[SchoolDemographicsHomeLanguageDto, ...] = ()


@dataclass(frozen=True)
class SchoolAttendanceLatestDto:
    academic_year: str
    overall_attendance_pct: float | None
    overall_absence_pct: float | None
    persistent_absence_pct: float | None


@dataclass(frozen=True)
class SchoolBehaviourLatestDto:
    academic_year: str
    suspensions_count: int | None
    suspensions_rate: float | None
    permanent_exclusions_count: int | None
    permanent_exclusions_rate: float | None


@dataclass(frozen=True)
class SchoolWorkforceLatestDto:
    academic_year: str
    pupil_teacher_ratio: float | None
    supply_staff_pct: float | None
    teachers_3plus_years_pct: float | None
    teacher_turnover_pct: float | None
    qts_pct: float | None
    qualifications_level6_plus_pct: float | None


@dataclass(frozen=True)
class SchoolLeadershipSnapshotDto:
    headteacher_name: str | None
    headteacher_start_date: date | None
    headteacher_tenure_years: float | None
    leadership_turnover_score: float | None


@dataclass(frozen=True)
class SchoolOfstedLatestDto:
    overall_effectiveness_code: str | None
    overall_effectiveness_label: str | None
    inspection_start_date: date | None
    publication_date: date | None
    latest_oeif_inspection_start_date: date | None
    latest_oeif_publication_date: date | None
    quality_of_education_code: str | None
    quality_of_education_label: str | None
    behaviour_and_attitudes_code: str | None
    behaviour_and_attitudes_label: str | None
    personal_development_code: str | None
    personal_development_label: str | None
    leadership_and_management_code: str | None
    leadership_and_management_label: str | None
    latest_ungraded_inspection_date: date | None
    latest_ungraded_publication_date: date | None
    most_recent_inspection_date: date | None
    days_since_most_recent_inspection: int | None
    is_graded: bool
    ungraded_outcome: str | None


@dataclass(frozen=True)
class SchoolOfstedTimelineEventDto:
    inspection_number: str
    inspection_start_date: date
    publication_date: date | None
    inspection_type: str | None
    overall_effectiveness_label: str | None
    headline_outcome_text: str | None
    category_of_concern: str | None


@dataclass(frozen=True)
class SchoolOfstedTimelineCoverageDto:
    is_partial_history: bool
    earliest_event_date: date | None
    latest_event_date: date | None
    events_count: int


@dataclass(frozen=True)
class SchoolOfstedTimelineDto:
    events: tuple[SchoolOfstedTimelineEventDto, ...]
    coverage: SchoolOfstedTimelineCoverageDto


@dataclass(frozen=True)
class SchoolAreaDeprivationDto:
    lsoa_code: str
    imd_score: float
    imd_rank: int
    imd_decile: int
    idaci_score: float
    idaci_decile: int
    income_score: float | None
    income_rank: int | None
    income_decile: int | None
    employment_score: float | None
    employment_rank: int | None
    employment_decile: int | None
    education_score: float | None
    education_rank: int | None
    education_decile: int | None
    health_score: float | None
    health_rank: int | None
    health_decile: int | None
    crime_score: float | None
    crime_rank: int | None
    crime_decile: int | None
    barriers_score: float | None
    barriers_rank: int | None
    barriers_decile: int | None
    living_environment_score: float | None
    living_environment_rank: int | None
    living_environment_decile: int | None
    population_total: int | None
    local_authority_district_code: str | None
    local_authority_district_name: str | None
    source_release: str


@dataclass(frozen=True)
class SchoolAreaCrimeCategoryDto:
    category: str
    incident_count: int


@dataclass(frozen=True)
class SchoolAreaCrimeDto:
    radius_miles: float
    latest_month: str
    total_incidents: int
    population_denominator: int | None
    incidents_per_1000: float | None
    annual_incidents_per_1000: tuple["SchoolAreaCrimeAnnualRateDto", ...]
    categories: tuple[SchoolAreaCrimeCategoryDto, ...]


@dataclass(frozen=True)
class SchoolAreaCrimeAnnualRateDto:
    year: int
    total_incidents: int
    incidents_per_1000: float | None


@dataclass(frozen=True)
class SchoolAreaHousePricePointDto:
    month: str
    average_price: float
    annual_change_pct: float | None
    monthly_change_pct: float | None


@dataclass(frozen=True)
class SchoolAreaHousePricesDto:
    area_code: str
    area_name: str
    latest_month: str
    average_price: float
    annual_change_pct: float | None
    monthly_change_pct: float | None
    three_year_change_pct: float | None
    trend: tuple[SchoolAreaHousePricePointDto, ...]


@dataclass(frozen=True)
class SchoolAreaContextCoverageDto:
    has_deprivation: bool
    has_crime: bool
    crime_months_available: int
    has_house_prices: bool
    house_price_months_available: int


@dataclass(frozen=True)
class SchoolAreaContextDto:
    deprivation: SchoolAreaDeprivationDto | None
    crime: SchoolAreaCrimeDto | None
    house_prices: SchoolAreaHousePricesDto | None
    coverage: SchoolAreaContextCoverageDto


@dataclass(frozen=True)
class SchoolPerformanceYearDto:
    academic_year: str
    attainment8_average: float | None
    progress8_average: float | None
    progress8_disadvantaged: float | None
    progress8_not_disadvantaged: float | None
    progress8_disadvantaged_gap: float | None
    engmath_5_plus_pct: float | None
    engmath_4_plus_pct: float | None
    ebacc_entry_pct: float | None
    ebacc_5_plus_pct: float | None
    ebacc_4_plus_pct: float | None
    ks2_reading_expected_pct: float | None
    ks2_writing_expected_pct: float | None
    ks2_maths_expected_pct: float | None
    ks2_combined_expected_pct: float | None
    ks2_reading_higher_pct: float | None
    ks2_writing_higher_pct: float | None
    ks2_maths_higher_pct: float | None
    ks2_combined_higher_pct: float | None


@dataclass(frozen=True)
class SchoolPerformanceDto:
    latest: SchoolPerformanceYearDto | None
    history: tuple[SchoolPerformanceYearDto, ...]


@dataclass(frozen=True)
class SchoolProfileMetricBenchmarkDto:
    metric_key: str
    academic_year: str
    school_value: float | int | None
    national_value: float | None
    local_value: float | None
    school_vs_national_delta: float | None
    school_vs_local_delta: float | None
    local_scope: Literal["local_authority_district", "phase"]
    local_area_code: str
    local_area_label: str


@dataclass(frozen=True)
class SchoolProfileBenchmarksDto:
    metrics: tuple[SchoolProfileMetricBenchmarkDto, ...]


@dataclass(frozen=True)
class SchoolProfileSectionCompletenessDto:
    status: SectionCompletenessStatus
    reason_code: SectionCompletenessReasonCode | None
    last_updated_at: datetime | None
    years_available: tuple[str, ...] | None = None


@dataclass(frozen=True)
class SchoolProfileCompletenessDto:
    demographics: SchoolProfileSectionCompletenessDto
    attendance: SchoolProfileSectionCompletenessDto
    behaviour: SchoolProfileSectionCompletenessDto
    workforce: SchoolProfileSectionCompletenessDto
    leadership: SchoolProfileSectionCompletenessDto
    performance: SchoolProfileSectionCompletenessDto
    ofsted_latest: SchoolProfileSectionCompletenessDto
    ofsted_timeline: SchoolProfileSectionCompletenessDto
    area_deprivation: SchoolProfileSectionCompletenessDto
    area_crime: SchoolProfileSectionCompletenessDto
    area_house_prices: SchoolProfileSectionCompletenessDto


@dataclass(frozen=True)
class SchoolProfileResponseDto:
    school: SchoolProfileSchoolDto
    demographics_latest: SchoolDemographicsLatestDto | None
    attendance_latest: SchoolAttendanceLatestDto | None
    behaviour_latest: SchoolBehaviourLatestDto | None
    workforce_latest: SchoolWorkforceLatestDto | None
    leadership_snapshot: SchoolLeadershipSnapshotDto | None
    performance: SchoolPerformanceDto | None
    ofsted_latest: SchoolOfstedLatestDto | None
    ofsted_timeline: SchoolOfstedTimelineDto | None
    area_context: SchoolAreaContextDto | None
    completeness: SchoolProfileCompletenessDto
    benchmarks: SchoolProfileBenchmarksDto = field(
        default_factory=lambda: SchoolProfileBenchmarksDto(metrics=())
    )
