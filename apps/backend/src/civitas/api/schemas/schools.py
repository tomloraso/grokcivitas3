from pydantic import BaseModel


class SchoolsSearchQueryResponse(BaseModel):
    postcode: str
    radius_miles: float
    phases: list[str]
    sort: str


class SchoolsSearchCenterResponse(BaseModel):
    lat: float
    lng: float


class SchoolSearchItemResponse(BaseModel):
    urn: str
    name: str
    type: str | None
    phase: str | None
    postcode: str | None
    lat: float
    lng: float
    distance_miles: float


class SchoolSearchLatestOfstedResponse(BaseModel):
    label: str | None
    sort_rank: int | None
    availability: str


class SchoolSearchAcademicMetricResponse(BaseModel):
    metric_key: str | None
    label: str | None
    display_value: str | None
    sort_value: float | None
    availability: str


class PostcodeSchoolSearchItemResponse(BaseModel):
    urn: str
    name: str
    type: str | None
    phase: str | None
    postcode: str | None
    lat: float
    lng: float
    distance_miles: float
    pupil_count: int | None
    latest_ofsted: SchoolSearchLatestOfstedResponse
    academic_metric: SchoolSearchAcademicMetricResponse


class SchoolsSearchResponse(BaseModel):
    query: SchoolsSearchQueryResponse
    center: SchoolsSearchCenterResponse
    count: int
    schools: list[PostcodeSchoolSearchItemResponse]


class SchoolNameSearchResponse(BaseModel):
    count: int
    schools: list[SchoolSearchItemResponse]
