from dataclasses import dataclass


@dataclass(frozen=True)
class PostcodeCoordinates:
    postcode: str
    lat: float
    lng: float
    lsoa: str | None
    admin_district: str | None
    lsoa_code: str | None = None


@dataclass(frozen=True)
class SchoolSearchResult:
    urn: str
    name: str
    school_type: str | None
    phase: str | None
    postcode: str | None
    lat: float
    lng: float
    distance_miles: float
