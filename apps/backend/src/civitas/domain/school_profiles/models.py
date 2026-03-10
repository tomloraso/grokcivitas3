from dataclasses import dataclass
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
class SchoolProfileSchool:
    urn: str
    name: str
    phase: str | None
    school_type: str | None
    status: str | None
    postcode: str | None
    website: str | None
    telephone: str | None
    head_title: str | None
    head_first_name: str | None
    head_last_name: str | None
    head_job_title: str | None
    address_street: str | None
    address_locality: str | None
    address_line3: str | None
    address_town: str | None
    address_county: str | None
    statutory_low_age: int | None
    statutory_high_age: int | None
    gender: str | None
    religious_character: str | None
    diocese: str | None
    admissions_policy: str | None
    sixth_form: str | None
    nursery_provision: str | None
    boarders: str | None
    fsm_pct_gias: float | None
    trust_name: str | None
    trust_flag: str | None
    federation_name: str | None
    federation_flag: str | None
    la_name: str | None
    la_code: str | None
    urban_rural: str | None
    number_of_boys: int | None
    number_of_girls: int | None
    lsoa_code: str | None
    lsoa_name: str | None
    last_changed_date: date | None
    lat: float
    lng: float


@dataclass(frozen=True)
class SchoolDemographicsCoverage:
    fsm_supported: bool
    ethnicity_supported: bool
    top_languages_supported: bool
    fsm6_supported: bool = False
    gender_supported: bool = False
    mobility_supported: bool = False
    send_primary_need_supported: bool = False


@dataclass(frozen=True)
class SchoolDemographicsEthnicityGroup:
    key: str
    label: str
    percentage: float | None
    count: int | None


@dataclass(frozen=True)
class SchoolDemographicsSendPrimaryNeed:
    key: str
    label: str
    percentage: float | None
    count: int | None


@dataclass(frozen=True)
class SchoolDemographicsHomeLanguage:
    key: str
    label: str
    rank: int
    percentage: float | None
    count: int | None


@dataclass(frozen=True)
class SchoolDemographicsLatest:
    academic_year: str
    disadvantaged_pct: float | None
    fsm_pct: float | None
    sen_pct: float | None
    ehcp_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None
    coverage: SchoolDemographicsCoverage
    fsm6_pct: float | None = None
    male_pct: float | None = None
    female_pct: float | None = None
    pupil_mobility_pct: float | None = None
    ethnicity_breakdown: tuple[SchoolDemographicsEthnicityGroup, ...] = ()
    send_primary_needs: tuple[SchoolDemographicsSendPrimaryNeed, ...] = ()
    top_home_languages: tuple[SchoolDemographicsHomeLanguage, ...] = ()


@dataclass(frozen=True)
class SchoolAttendanceLatest:
    academic_year: str
    overall_attendance_pct: float | None
    overall_absence_pct: float | None
    persistent_absence_pct: float | None


@dataclass(frozen=True)
class SchoolBehaviourLatest:
    academic_year: str
    suspensions_count: int | None
    suspensions_rate: float | None
    permanent_exclusions_count: int | None
    permanent_exclusions_rate: float | None


@dataclass(frozen=True)
class SchoolWorkforceBreakdownItem:
    key: str
    label: str
    headcount: float | None
    fte: float | None = None
    headcount_pct: float | None = None
    fte_pct: float | None = None


@dataclass(frozen=True)
class SchoolWorkforceLatest:
    academic_year: str
    pupil_teacher_ratio: float | None
    supply_staff_pct: float | None
    teachers_3plus_years_pct: float | None
    teacher_turnover_pct: float | None
    qts_pct: float | None
    qualifications_level6_plus_pct: float | None
    teacher_headcount_total: float | None = None
    teacher_fte_total: float | None = None
    support_staff_headcount_total: float | None = None
    support_staff_fte_total: float | None = None
    leadership_headcount: float | None = None
    teacher_average_mean_salary_gbp: float | None = None
    teacher_absence_pct: float | None = None
    teacher_vacancy_rate: float | None = None
    third_party_support_staff_headcount: float | None = None
    teacher_sex_breakdown: tuple[SchoolWorkforceBreakdownItem, ...] = ()
    teacher_age_breakdown: tuple[SchoolWorkforceBreakdownItem, ...] = ()
    teacher_ethnicity_breakdown: tuple[SchoolWorkforceBreakdownItem, ...] = ()
    teacher_qualification_breakdown: tuple[SchoolWorkforceBreakdownItem, ...] = ()
    support_staff_post_mix: tuple[SchoolWorkforceBreakdownItem, ...] = ()


@dataclass(frozen=True)
class SchoolFinanceLatest:
    academic_year: str
    total_income_gbp: float | None
    total_expenditure_gbp: float | None
    income_per_pupil_gbp: float | None
    expenditure_per_pupil_gbp: float | None
    total_staff_costs_gbp: float | None
    staff_costs_pct_of_expenditure: float | None
    revenue_reserve_gbp: float | None
    revenue_reserve_per_pupil_gbp: float | None


@dataclass(frozen=True)
class SchoolLeadershipSnapshot:
    headteacher_name: str | None
    headteacher_start_date: date | None
    headteacher_tenure_years: float | None
    leadership_turnover_score: float | None


@dataclass(frozen=True)
class SchoolOfstedLatest:
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
    provider_page_url: str | None = None


@dataclass(frozen=True)
class SchoolOfstedTimelineEvent:
    inspection_number: str
    inspection_start_date: date
    publication_date: date | None
    inspection_type: str | None
    overall_effectiveness_label: str | None
    headline_outcome_text: str | None
    category_of_concern: str | None


@dataclass(frozen=True)
class SchoolOfstedTimelineCoverage:
    is_partial_history: bool
    earliest_event_date: date | None
    latest_event_date: date | None
    events_count: int


@dataclass(frozen=True)
class SchoolOfstedTimeline:
    events: tuple[SchoolOfstedTimelineEvent, ...]
    coverage: SchoolOfstedTimelineCoverage


@dataclass(frozen=True)
class SchoolAreaDeprivation:
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
class SchoolAreaCrimeCategory:
    category: str
    incident_count: int


@dataclass(frozen=True)
class SchoolAreaCrime:
    radius_miles: float
    latest_month: str
    total_incidents: int
    population_denominator: int | None
    incidents_per_1000: float | None
    annual_incidents_per_1000: tuple["SchoolAreaCrimeAnnualRate", ...]
    categories: tuple[SchoolAreaCrimeCategory, ...]


@dataclass(frozen=True)
class SchoolAreaCrimeAnnualRate:
    year: int
    total_incidents: int
    incidents_per_1000: float | None


@dataclass(frozen=True)
class SchoolAreaHousePricePoint:
    month: str
    average_price: float
    annual_change_pct: float | None
    monthly_change_pct: float | None


@dataclass(frozen=True)
class SchoolAreaHousePrices:
    area_code: str
    area_name: str
    latest_month: str
    average_price: float
    annual_change_pct: float | None
    monthly_change_pct: float | None
    three_year_change_pct: float | None
    trend: tuple[SchoolAreaHousePricePoint, ...]


@dataclass(frozen=True)
class SchoolAreaContextCoverage:
    has_deprivation: bool
    has_crime: bool
    crime_months_available: int
    has_house_prices: bool
    house_price_months_available: int


@dataclass(frozen=True)
class SchoolAreaContext:
    deprivation: SchoolAreaDeprivation | None
    crime: SchoolAreaCrime | None
    house_prices: SchoolAreaHousePrices | None
    coverage: SchoolAreaContextCoverage


@dataclass(frozen=True)
class SchoolPerformanceYear:
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
class SchoolPerformance:
    latest: SchoolPerformanceYear | None
    history: tuple[SchoolPerformanceYear, ...]


@dataclass(frozen=True)
class SchoolProfileSectionCompleteness:
    status: SectionCompletenessStatus
    reason_code: SectionCompletenessReasonCode | None
    last_updated_at: datetime | None
    years_available: tuple[str, ...] | None = None


@dataclass(frozen=True)
class SchoolProfileCompleteness:
    demographics: SchoolProfileSectionCompleteness
    attendance: SchoolProfileSectionCompleteness
    behaviour: SchoolProfileSectionCompleteness
    workforce: SchoolProfileSectionCompleteness
    finance: SchoolProfileSectionCompleteness
    leadership: SchoolProfileSectionCompleteness
    performance: SchoolProfileSectionCompleteness
    ofsted_latest: SchoolProfileSectionCompleteness
    ofsted_timeline: SchoolProfileSectionCompleteness
    area_deprivation: SchoolProfileSectionCompleteness
    area_crime: SchoolProfileSectionCompleteness
    area_house_prices: SchoolProfileSectionCompleteness


@dataclass(frozen=True)
class SchoolProfile:
    school: SchoolProfileSchool
    demographics_latest: SchoolDemographicsLatest | None
    attendance_latest: SchoolAttendanceLatest | None
    behaviour_latest: SchoolBehaviourLatest | None
    workforce_latest: SchoolWorkforceLatest | None
    finance_latest: SchoolFinanceLatest | None
    leadership_snapshot: SchoolLeadershipSnapshot | None
    performance: SchoolPerformance | None
    ofsted_latest: SchoolOfstedLatest | None
    ofsted_timeline: SchoolOfstedTimeline | None
    area_context: SchoolAreaContext | None
    completeness: SchoolProfileCompleteness
