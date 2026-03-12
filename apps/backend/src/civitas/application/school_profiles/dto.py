from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

from civitas.application.access.dto import SectionAccessDto
from civitas.application.favourites.dto import (
    SavedSchoolStateDto,
    anonymous_saved_school_state,
)
from civitas.application.subject_performance.dto import SchoolSubjectPerformanceLatestDto

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
    "unsupported_stage",
]


@dataclass(frozen=True)
class SchoolProfileSchoolDto:
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
class SchoolWorkforceBreakdownItemDto:
    key: str
    label: str
    headcount: float | None
    fte: float | None = None
    headcount_pct: float | None = None
    fte_pct: float | None = None


@dataclass(frozen=True)
class SchoolWorkforceLatestDto:
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
    teacher_sex_breakdown: tuple[SchoolWorkforceBreakdownItemDto, ...] = ()
    teacher_age_breakdown: tuple[SchoolWorkforceBreakdownItemDto, ...] = ()
    teacher_ethnicity_breakdown: tuple[SchoolWorkforceBreakdownItemDto, ...] = ()
    teacher_qualification_breakdown: tuple[SchoolWorkforceBreakdownItemDto, ...] = ()
    support_staff_post_mix: tuple[SchoolWorkforceBreakdownItemDto, ...] = ()


@dataclass(frozen=True)
class SchoolFinanceLatestDto:
    academic_year: str
    total_income_gbp: float | None
    total_expenditure_gbp: float | None
    income_per_pupil_gbp: float | None
    expenditure_per_pupil_gbp: float | None
    total_staff_costs_gbp: float | None
    staff_costs_pct_of_expenditure: float | None
    revenue_reserve_gbp: float | None
    revenue_reserve_per_pupil_gbp: float | None
    in_year_balance_gbp: float | None
    total_grant_funding_gbp: float | None
    total_self_generated_funding_gbp: float | None
    teaching_staff_costs_gbp: float | None
    supply_teaching_staff_costs_gbp: float | None
    education_support_staff_costs_gbp: float | None
    other_staff_costs_gbp: float | None
    premises_costs_gbp: float | None
    educational_supplies_costs_gbp: float | None
    bought_in_professional_services_costs_gbp: float | None
    catering_costs_gbp: float | None
    supply_staff_costs_pct_of_staff_costs: float | None


@dataclass(frozen=True)
class SchoolAdmissionsLatestDto:
    academic_year: str
    places_offered_total: int | None
    applications_any_preference: int | None
    applications_first_preference: int | None
    oversubscription_ratio: float | None
    first_preference_offer_rate: float | None
    any_preference_offer_rate: float | None
    admissions_policy: str | None


@dataclass(frozen=True)
class SchoolDestinationStageLatestDto:
    academic_year: str
    cohort_count: int | None
    qualification_group: str | None
    qualification_level: str | None
    overall_pct: float | None
    education_pct: float | None
    apprenticeship_pct: float | None
    employment_pct: float | None
    not_sustained_pct: float | None
    activity_unknown_pct: float | None
    fe_pct: float | None
    other_education_pct: float | None
    school_sixth_form_pct: float | None = None
    sixth_form_college_pct: float | None = None
    higher_education_pct: float | None = None


@dataclass(frozen=True)
class SchoolDestinationsLatestDto:
    ks4: SchoolDestinationStageLatestDto | None
    study_16_18: SchoolDestinationStageLatestDto | None


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
    provider_page_url: str | None = None


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
class SchoolProfileAnalystSectionDto:
    access: SectionAccessDto
    text: str | None = None
    teaser_text: str | None = None
    disclaimer: str | None = None


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
class SchoolBenchmarkContextDto:
    scope: Literal["national", "local_authority_district", "phase", "similar_school"]
    label: str
    value: float | None
    percentile_rank: float | None
    school_count: int | None
    area_code: str | None = None


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
    contexts: tuple[SchoolBenchmarkContextDto, ...] = ()


@dataclass(frozen=True)
class SchoolProfileBenchmarksDto:
    metrics: tuple[SchoolProfileMetricBenchmarkDto, ...]


@dataclass(frozen=True)
class SchoolProfileNeighbourhoodSectionDto:
    access: SectionAccessDto
    area_context: SchoolAreaContextDto | None = None
    teaser_text: str | None = None


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
    admissions: SchoolProfileSectionCompletenessDto
    destinations: SchoolProfileSectionCompletenessDto
    finance: SchoolProfileSectionCompletenessDto
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
    overview_text: str | None
    analyst: SchoolProfileAnalystSectionDto
    demographics_latest: SchoolDemographicsLatestDto | None
    attendance_latest: SchoolAttendanceLatestDto | None
    behaviour_latest: SchoolBehaviourLatestDto | None
    workforce_latest: SchoolWorkforceLatestDto | None
    admissions_latest: SchoolAdmissionsLatestDto | None
    destinations_latest: SchoolDestinationsLatestDto | None
    finance_latest: SchoolFinanceLatestDto | None
    leadership_snapshot: SchoolLeadershipSnapshotDto | None
    performance: SchoolPerformanceDto | None
    ofsted_latest: SchoolOfstedLatestDto | None
    ofsted_timeline: SchoolOfstedTimelineDto | None
    neighbourhood: SchoolProfileNeighbourhoodSectionDto
    completeness: SchoolProfileCompletenessDto
    subject_performance: SchoolSubjectPerformanceLatestDto | None = None
    saved_state: SavedSchoolStateDto = field(default_factory=anonymous_saved_school_state)
    benchmarks: SchoolProfileBenchmarksDto = field(
        default_factory=lambda: SchoolProfileBenchmarksDto(metrics=())
    )
