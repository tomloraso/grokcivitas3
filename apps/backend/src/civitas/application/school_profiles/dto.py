from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

SectionCompletenessStatus = Literal["available", "partial", "unavailable"]
SectionCompletenessReasonCode = Literal[
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


@dataclass(frozen=True)
class SchoolOfstedLatestDto:
    overall_effectiveness_code: str | None
    overall_effectiveness_label: str | None
    inspection_start_date: date | None
    publication_date: date | None
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
    imd_decile: int
    idaci_score: float
    idaci_decile: int
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
    categories: tuple[SchoolAreaCrimeCategoryDto, ...]


@dataclass(frozen=True)
class SchoolAreaContextCoverageDto:
    has_deprivation: bool
    has_crime: bool
    crime_months_available: int


@dataclass(frozen=True)
class SchoolAreaContextDto:
    deprivation: SchoolAreaDeprivationDto | None
    crime: SchoolAreaCrimeDto | None
    coverage: SchoolAreaContextCoverageDto


@dataclass(frozen=True)
class SchoolProfileSectionCompletenessDto:
    status: SectionCompletenessStatus
    reason_code: SectionCompletenessReasonCode | None
    last_updated_at: datetime | None
    years_available: tuple[str, ...] | None = None


@dataclass(frozen=True)
class SchoolProfileCompletenessDto:
    demographics: SchoolProfileSectionCompletenessDto
    ofsted_latest: SchoolProfileSectionCompletenessDto
    ofsted_timeline: SchoolProfileSectionCompletenessDto
    area_deprivation: SchoolProfileSectionCompletenessDto
    area_crime: SchoolProfileSectionCompletenessDto


@dataclass(frozen=True)
class SchoolProfileResponseDto:
    school: SchoolProfileSchoolDto
    demographics_latest: SchoolDemographicsLatestDto | None
    ofsted_latest: SchoolOfstedLatestDto | None
    ofsted_timeline: SchoolOfstedTimelineDto | None
    area_context: SchoolAreaContextDto | None
    completeness: SchoolProfileCompletenessDto
