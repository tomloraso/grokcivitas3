from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class SchoolProfileSchoolResponse(BaseModel):
    urn: str
    name: str
    phase: str | None
    type: str | None
    status: str | None
    postcode: str | None
    lat: float
    lng: float


class SchoolProfileDemographicsCoverageResponse(BaseModel):
    fsm_supported: bool
    ethnicity_supported: bool
    top_languages_supported: bool


class SchoolProfileDemographicsEthnicityGroupResponse(BaseModel):
    key: str
    label: str
    percentage: float | None
    count: int | None


class SchoolProfileDemographicsLatestResponse(BaseModel):
    academic_year: str
    disadvantaged_pct: float | None
    fsm_pct: float | None
    sen_pct: float | None
    ehcp_pct: float | None
    eal_pct: float | None
    first_language_english_pct: float | None
    first_language_unclassified_pct: float | None
    coverage: SchoolProfileDemographicsCoverageResponse
    ethnicity_breakdown: list[SchoolProfileDemographicsEthnicityGroupResponse] = Field(
        default_factory=list
    )


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
    source_release: str


class SchoolProfileAreaCrimeCategoryResponse(BaseModel):
    category: str
    incident_count: int


class SchoolProfileAreaCrimeResponse(BaseModel):
    radius_miles: float
    latest_month: str
    total_incidents: int
    categories: list[SchoolProfileAreaCrimeCategoryResponse]


class SchoolProfileAreaContextCoverageResponse(BaseModel):
    has_deprivation: bool
    has_crime: bool
    crime_months_available: int


class SchoolProfileAreaContextResponse(BaseModel):
    deprivation: SchoolProfileAreaDeprivationResponse | None
    crime: SchoolProfileAreaCrimeResponse | None
    coverage: SchoolProfileAreaContextCoverageResponse


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
    performance: SchoolProfileSectionCompletenessResponse
    ofsted_latest: SchoolProfileSectionCompletenessResponse
    ofsted_timeline: SchoolProfileSectionCompletenessResponse
    area_deprivation: SchoolProfileSectionCompletenessResponse
    area_crime: SchoolProfileSectionCompletenessResponse


class SchoolProfileResponse(BaseModel):
    school: SchoolProfileSchoolResponse
    demographics_latest: SchoolProfileDemographicsLatestResponse | None
    performance: SchoolProfilePerformanceResponse | None
    ofsted_latest: SchoolProfileOfstedLatestResponse | None
    ofsted_timeline: SchoolProfileOfstedTimelineResponse
    area_context: SchoolProfileAreaContextResponse
    completeness: SchoolProfileCompletenessResponse
