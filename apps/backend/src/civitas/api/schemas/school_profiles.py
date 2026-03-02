from datetime import date

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


class SchoolProfileResponse(BaseModel):
    school: SchoolProfileSchoolResponse
    demographics_latest: SchoolProfileDemographicsLatestResponse | None
    ofsted_latest: SchoolProfileOfstedLatestResponse | None
