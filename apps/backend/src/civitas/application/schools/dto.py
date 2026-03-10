from dataclasses import dataclass, field

from civitas.application.favourites.dto import (
    SavedSchoolStateDto,
    anonymous_saved_school_state,
)


@dataclass(frozen=True)
class PostcodeSchoolSearchLatestOfstedDto:
    label: str | None
    sort_rank: int | None
    availability: str


@dataclass(frozen=True)
class PostcodeSchoolSearchAcademicMetricDto:
    metric_key: str | None
    label: str | None
    display_value: str | None
    sort_value: float | None
    availability: str


@dataclass(frozen=True)
class PostcodeSchoolSearchItemDto:
    urn: str
    name: str
    school_type: str | None
    phase: str | None
    postcode: str | None
    lat: float
    lng: float
    distance_miles: float
    pupil_count: int | None
    latest_ofsted: PostcodeSchoolSearchLatestOfstedDto
    academic_metric: PostcodeSchoolSearchAcademicMetricDto
    saved_state: SavedSchoolStateDto = field(default_factory=anonymous_saved_school_state)


@dataclass(frozen=True)
class SchoolNameSearchItemDto:
    urn: str
    name: str
    school_type: str | None
    phase: str | None
    postcode: str | None
    lat: float
    lng: float
    distance_miles: float
    saved_state: SavedSchoolStateDto = field(default_factory=anonymous_saved_school_state)


@dataclass(frozen=True)
class SchoolSearchQueryDto:
    postcode: str
    radius_miles: float
    phases: tuple[str, ...] = ()
    sort: str = "closest"


@dataclass(frozen=True)
class SearchCenterDto:
    lat: float
    lng: float


@dataclass(frozen=True)
class SchoolsSearchResponseDto:
    query: SchoolSearchQueryDto
    center: SearchCenterDto
    schools: tuple[PostcodeSchoolSearchItemDto, ...]

    @property
    def count(self) -> int:
        return len(self.schools)


@dataclass(frozen=True)
class SchoolNameSearchResponseDto:
    schools: tuple[SchoolNameSearchItemDto, ...]

    @property
    def count(self) -> int:
        return len(self.schools)
