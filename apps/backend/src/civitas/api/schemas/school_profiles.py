from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from civitas.api.schemas.access import SectionAccessResponse


class SchoolProfileSchoolResponse(BaseModel):
    urn: str
    name: str
    phase: str | None
    type: str | None
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


class SchoolProfileDemographicsCoverageResponse(BaseModel):
    fsm_supported: bool
    fsm6_supported: bool
    gender_supported: bool
    mobility_supported: bool
    send_primary_need_supported: bool
    ethnicity_supported: bool
    top_languages_supported: bool


class SchoolProfileDemographicsEthnicityGroupResponse(BaseModel):
    key: str
    label: str
    percentage: float | None
    count: int | None


class SchoolProfileDemographicsSendPrimaryNeedResponse(BaseModel):
    key: str
    label: str
    percentage: float | None
    count: int | None


class SchoolProfileDemographicsHomeLanguageResponse(BaseModel):
    key: str
    label: str
    rank: int
    percentage: float | None
    count: int | None


class SchoolProfileDemographicsLatestResponse(BaseModel):
    academic_year: str
    disadvantaged_pct: float | None
    fsm_pct: float | None
    fsm6_pct: float | None = None
    sen_pct: float | None
    ehcp_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None
    male_pct: float | None = None
    female_pct: float | None = None
    pupil_mobility_pct: float | None = None
    coverage: SchoolProfileDemographicsCoverageResponse
    ethnicity_breakdown: list[SchoolProfileDemographicsEthnicityGroupResponse] = Field(
        default_factory=list
    )
    send_primary_needs: list[SchoolProfileDemographicsSendPrimaryNeedResponse] = Field(
        default_factory=list
    )
    top_home_languages: list[SchoolProfileDemographicsHomeLanguageResponse] = Field(
        default_factory=list
    )


class SchoolProfileAttendanceLatestResponse(BaseModel):
    academic_year: str
    overall_attendance_pct: float | None
    overall_absence_pct: float | None
    persistent_absence_pct: float | None


class SchoolProfileBehaviourLatestResponse(BaseModel):
    academic_year: str
    suspensions_count: int | None
    suspensions_rate: float | None
    permanent_exclusions_count: int | None
    permanent_exclusions_rate: float | None


class SchoolProfileWorkforceLatestResponse(BaseModel):
    academic_year: str
    pupil_teacher_ratio: float | None
    supply_staff_pct: float | None
    teachers_3plus_years_pct: float | None
    teacher_turnover_pct: float | None
    qts_pct: float | None
    qualifications_level6_plus_pct: float | None


class SchoolProfileLeadershipSnapshotResponse(BaseModel):
    headteacher_name: str | None
    headteacher_start_date: date | None
    headteacher_tenure_years: float | None
    leadership_turnover_score: float | None


class SchoolProfileOfstedLatestResponse(BaseModel):
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


class SchoolProfileOfstedTimelineEventResponse(BaseModel):
    inspection_number: str
    inspection_start_date: date
    publication_date: date | None
    inspection_type: str | None
    overall_effectiveness_label: str | None
    headline_outcome_text: str | None
    category_of_concern: str | None


class SchoolProfileOfstedTimelineCoverageResponse(BaseModel):
    is_partial_history: bool
    earliest_event_date: date | None
    latest_event_date: date | None
    events_count: int


class SchoolProfileOfstedTimelineResponse(BaseModel):
    events: list[SchoolProfileOfstedTimelineEventResponse]
    coverage: SchoolProfileOfstedTimelineCoverageResponse


class SchoolProfileAreaDeprivationResponse(BaseModel):
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


class SchoolProfileAreaCrimeCategoryResponse(BaseModel):
    category: str
    incident_count: int


class SchoolProfileAreaCrimeAnnualRateResponse(BaseModel):
    year: int
    total_incidents: int
    incidents_per_1000: float | None


class SchoolProfileAreaCrimeResponse(BaseModel):
    radius_miles: float
    latest_month: str
    total_incidents: int
    population_denominator: int | None
    incidents_per_1000: float | None
    annual_incidents_per_1000: list[SchoolProfileAreaCrimeAnnualRateResponse]
    categories: list[SchoolProfileAreaCrimeCategoryResponse]


class SchoolProfileAreaHousePricePointResponse(BaseModel):
    month: str
    average_price: float
    annual_change_pct: float | None
    monthly_change_pct: float | None


class SchoolProfileAreaHousePricesResponse(BaseModel):
    area_code: str
    area_name: str
    latest_month: str
    average_price: float
    annual_change_pct: float | None
    monthly_change_pct: float | None
    three_year_change_pct: float | None
    trend: list[SchoolProfileAreaHousePricePointResponse]


class SchoolProfileAreaContextCoverageResponse(BaseModel):
    has_deprivation: bool
    has_crime: bool
    crime_months_available: int
    has_house_prices: bool
    house_price_months_available: int


class SchoolProfileAreaContextResponse(BaseModel):
    deprivation: SchoolProfileAreaDeprivationResponse | None
    crime: SchoolProfileAreaCrimeResponse | None
    house_prices: SchoolProfileAreaHousePricesResponse | None
    coverage: SchoolProfileAreaContextCoverageResponse


class SchoolProfileAnalystSectionResponse(BaseModel):
    access: SectionAccessResponse
    text: str | None
    teaser_text: str | None
    disclaimer: str | None


class SchoolProfilePerformanceYearResponse(BaseModel):
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


class SchoolProfilePerformanceResponse(BaseModel):
    latest: SchoolProfilePerformanceYearResponse | None
    history: list[SchoolProfilePerformanceYearResponse] = Field(default_factory=list)


class SchoolProfileMetricBenchmarkResponse(BaseModel):
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


class SchoolProfileBenchmarksResponse(BaseModel):
    metrics: list[SchoolProfileMetricBenchmarkResponse] = Field(default_factory=list)


class SchoolProfileNeighbourhoodSectionResponse(BaseModel):
    access: SectionAccessResponse
    area_context: SchoolProfileAreaContextResponse | None
    teaser_text: str | None


class SchoolProfileSectionCompletenessResponse(BaseModel):
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
            "source_coverage_gap",
            "stale_after_school_refresh",
            "no_incidents_in_radius",
        ]
        | None
    )
    last_updated_at: datetime | None
    years_available: list[str] | None = None


class SchoolProfileCompletenessResponse(BaseModel):
    demographics: SchoolProfileSectionCompletenessResponse
    attendance: SchoolProfileSectionCompletenessResponse
    behaviour: SchoolProfileSectionCompletenessResponse
    workforce: SchoolProfileSectionCompletenessResponse
    leadership: SchoolProfileSectionCompletenessResponse
    performance: SchoolProfileSectionCompletenessResponse
    ofsted_latest: SchoolProfileSectionCompletenessResponse
    ofsted_timeline: SchoolProfileSectionCompletenessResponse
    area_deprivation: SchoolProfileSectionCompletenessResponse
    area_crime: SchoolProfileSectionCompletenessResponse
    area_house_prices: SchoolProfileSectionCompletenessResponse


class SchoolProfileResponse(BaseModel):
    school: SchoolProfileSchoolResponse
    overview_text: str | None
    analyst: SchoolProfileAnalystSectionResponse
    demographics_latest: SchoolProfileDemographicsLatestResponse | None
    attendance_latest: SchoolProfileAttendanceLatestResponse | None
    behaviour_latest: SchoolProfileBehaviourLatestResponse | None
    workforce_latest: SchoolProfileWorkforceLatestResponse | None
    leadership_snapshot: SchoolProfileLeadershipSnapshotResponse | None
    performance: SchoolProfilePerformanceResponse | None
    ofsted_latest: SchoolProfileOfstedLatestResponse | None
    ofsted_timeline: SchoolProfileOfstedTimelineResponse
    neighbourhood: SchoolProfileNeighbourhoodSectionResponse
    benchmarks: SchoolProfileBenchmarksResponse = Field(
        default_factory=SchoolProfileBenchmarksResponse
    )
    completeness: SchoolProfileCompletenessResponse
