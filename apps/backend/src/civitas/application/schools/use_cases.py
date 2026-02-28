from civitas.application.schools.dto import (
    SchoolSearchQueryDto,
    SchoolsSearchResponseDto,
    SearchCenterDto,
)
from civitas.application.schools.errors import InvalidSchoolSearchParametersError
from civitas.application.schools.ports.postcode_resolver import PostcodeResolver
from civitas.application.schools.ports.school_search_repository import SchoolSearchRepository
from civitas.domain.schools.value_objects import InvalidPostcodeError, normalize_uk_postcode

DEFAULT_RADIUS_MILES = 5.0
MAX_RADIUS_MILES = 25.0


class SearchSchoolsByPostcodeUseCase:
    def __init__(
        self,
        school_search_repository: SchoolSearchRepository,
        postcode_resolver: PostcodeResolver,
    ) -> None:
        self._school_search_repository = school_search_repository
        self._postcode_resolver = postcode_resolver

    def execute(
        self,
        *,
        postcode: str,
        radius_miles: float | None = None,
    ) -> SchoolsSearchResponseDto:
        normalized_postcode = _validate_and_normalize_postcode(postcode)
        resolved_radius = _validate_radius(radius_miles)
        center = self._postcode_resolver.resolve(normalized_postcode)
        schools = list(
            self._school_search_repository.search_within_radius(
                center_lat=center.lat,
                center_lng=center.lng,
                radius_miles=resolved_radius,
            )
        )
        schools.sort(key=lambda school: (school.distance_miles, school.urn))
        return SchoolsSearchResponseDto(
            query=SchoolSearchQueryDto(
                postcode=center.postcode,
                radius_miles=resolved_radius,
            ),
            center=SearchCenterDto(lat=center.lat, lng=center.lng),
            schools=tuple(schools),
        )


def _validate_and_normalize_postcode(postcode: str) -> str:
    if not isinstance(postcode, str):
        raise InvalidSchoolSearchParametersError("postcode must be a valid UK postcode.")
    try:
        return normalize_uk_postcode(postcode)
    except InvalidPostcodeError as exc:
        raise InvalidSchoolSearchParametersError(str(exc)) from exc


def _validate_radius(radius_miles: float | None) -> float:
    if radius_miles is None:
        return DEFAULT_RADIUS_MILES
    if radius_miles <= 0 or radius_miles > MAX_RADIUS_MILES:
        raise InvalidSchoolSearchParametersError("radius must be between 0 and 25 miles")
    return radius_miles
