from dataclasses import dataclass
from datetime import date


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
class SchoolProfileResponseDto:
    school: SchoolProfileSchoolDto
    demographics_latest: SchoolDemographicsLatestDto | None
    ofsted_latest: SchoolOfstedLatestDto | None
