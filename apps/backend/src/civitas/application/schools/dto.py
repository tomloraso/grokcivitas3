from dataclasses import dataclass

from civitas.domain.schools.models import SchoolSearchResult


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
    schools: tuple[SchoolSearchResult, ...]

    @property
    def count(self) -> int:
        return len(self.schools)
