from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


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


class SchoolProfileOfstedLatestResponse(BaseModel):
    overall_effectiveness_code: str | None
    overall_effectiveness_label: str | None
    inspection_start_date: date | None
    publication_date: date | None
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


class SchoolProfileSectionCompletenessResponse(BaseModel):
    status: Literal["available", "partial", "unavailable"]
    reason_code: (
        Literal[
            "source_missing",
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
    ofsted_latest: SchoolProfileSectionCompletenessResponse
    ofsted_timeline: SchoolProfileSectionCompletenessResponse
    area_deprivation: SchoolProfileSectionCompletenessResponse
    area_crime: SchoolProfileSectionCompletenessResponse


class SchoolProfileResponse(BaseModel):
    school: SchoolProfileSchoolResponse
    demographics_latest: SchoolProfileDemographicsLatestResponse | None
    ofsted_latest: SchoolProfileOfstedLatestResponse | None
    ofsted_timeline: SchoolProfileOfstedTimelineResponse
    area_context: SchoolProfileAreaContextResponse
    completeness: SchoolProfileCompletenessResponse
