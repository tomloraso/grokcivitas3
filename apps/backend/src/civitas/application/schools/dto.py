from dataclasses import dataclass

from civitas.domain.schools.models import SchoolSearchResult


@dataclass(frozen=True)
class SchoolSearchQueryDto:
    postcode: str
    radius_miles: float


@dataclass(frozen=True)
class SearchCenterDto:
    lat: float
    lng: float


@dataclass(frozen=True)
class SchoolsSearchResponseDto:
    query: SchoolSearchQueryDto
    center: SearchCenterDto
    schools: tuple[SchoolSearchResult, ...]

    @property
    def count(self) -> int:
        return len(self.schools)


@dataclass(frozen=True)
class SchoolNameSearchResponseDto:
    schools: tuple[SchoolSearchResult, ...]

    @property
    def count(self) -> int:
        return len(self.schools)
