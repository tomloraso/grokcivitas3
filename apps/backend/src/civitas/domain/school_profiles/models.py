from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SchoolProfileSchool:
    urn: str
    name: str
    phase: str | None
    school_type: str | None
    status: str | None
    postcode: str | None
    lat: float
    lng: float


@dataclass(frozen=True)
class SchoolDemographicsCoverage:
    fsm_supported: bool
    ethnicity_supported: bool
    top_languages_supported: bool


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


@dataclass(frozen=True)
class SchoolOfstedLatest:
    overall_effectiveness_code: str | None
    overall_effectiveness_label: str | None
    inspection_start_date: date | None
    publication_date: date | None
    is_graded: bool
    ungraded_outcome: str | None


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
    imd_decile: int
    idaci_score: float
    idaci_decile: int
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
    categories: tuple[SchoolAreaCrimeCategory, ...]


@dataclass(frozen=True)
class SchoolAreaContextCoverage:
    has_deprivation: bool
    has_crime: bool
    crime_months_available: int


@dataclass(frozen=True)
class SchoolAreaContext:
    deprivation: SchoolAreaDeprivation | None
    crime: SchoolAreaCrime | None
    coverage: SchoolAreaContextCoverage


@dataclass(frozen=True)
class SchoolProfile:
    school: SchoolProfileSchool
    demographics_latest: SchoolDemographicsLatest | None
    ofsted_latest: SchoolOfstedLatest | None
    ofsted_timeline: SchoolOfstedTimeline | None
    area_context: SchoolAreaContext | None
