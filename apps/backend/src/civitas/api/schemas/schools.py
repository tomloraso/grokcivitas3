from pydantic import BaseModel


class SchoolsSearchQueryResponse(BaseModel):
    postcode: str
    radius_miles: float


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


class SchoolsSearchResponse(BaseModel):
    query: SchoolsSearchQueryResponse
    center: SchoolsSearchCenterResponse
    count: int
    schools: list[SchoolSearchItemResponse]


class SchoolNameSearchResponse(BaseModel):
    count: int
    schools: list[SchoolSearchItemResponse]
