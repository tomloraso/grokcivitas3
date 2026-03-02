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
class SchoolProfile:
    school: SchoolProfileSchool
    demographics_latest: SchoolDemographicsLatest | None
    ofsted_latest: SchoolOfstedLatest | None
