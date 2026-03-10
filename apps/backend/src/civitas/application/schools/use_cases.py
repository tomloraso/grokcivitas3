from collections.abc import Sequence
from dataclasses import replace
from uuid import UUID

from civitas.application.favourites.dto import SavedSchoolStateDto, anonymous_saved_school_state
from civitas.application.favourites.ports.saved_school_state_resolver import (
    SavedSchoolStateResolver,
)
from civitas.application.schools.dto import (
    SchoolNameSearchResponseDto,
    SchoolSearchQueryDto,
    SchoolsSearchResponseDto,
    SearchCenterDto,
)
from civitas.application.schools.errors import InvalidSchoolSearchParametersError
from civitas.application.schools.ports.postcode_resolver import PostcodeResolver
from civitas.application.schools.ports.school_search_repository import SchoolSearchRepository
from civitas.application.schools.ports.school_search_summary_materializer import (
    SchoolSearchSummaryMaterializer,
)
from civitas.domain.schools.value_objects import InvalidPostcodeError, normalize_uk_postcode

DEFAULT_RADIUS_MILES = 5.0
MAX_RADIUS_MILES = 25.0
DEFAULT_NAME_SEARCH_LIMIT = 50
MIN_NAME_LENGTH = 3
DEFAULT_SORT = "closest"
VALID_SORTS = frozenset({"closest", "ofsted", "academic"})
VALID_PHASE_FILTERS = ("primary", "secondary")


class SearchSchoolsByPostcodeUseCase:
    def __init__(
        self,
        school_search_repository: SchoolSearchRepository,
        postcode_resolver: PostcodeResolver,
        saved_school_state_resolver: SavedSchoolStateResolver | None = None,
    ) -> None:
        self._school_search_repository = school_search_repository
        self._postcode_resolver = postcode_resolver
        self._saved_school_state_resolver = saved_school_state_resolver

    def execute(
        self,
        *,
        postcode: str,
        radius_miles: float | None = None,
        phases: Sequence[str] | None = None,
        sort: str | None = None,
        viewer_user_id: UUID | None = None,
    ) -> SchoolsSearchResponseDto:
        normalized_postcode = _validate_and_normalize_postcode(postcode)
        resolved_radius = _validate_radius(radius_miles)
        resolved_phases = _validate_phase_filters(phases)
        resolved_sort = _validate_sort(sort, resolved_phases)
        center = self._postcode_resolver.resolve(normalized_postcode)
        schools = tuple(
            self._school_search_repository.search_within_radius(
                center_lat=center.lat,
                center_lng=center.lng,
                radius_miles=resolved_radius,
                phase_filters=resolved_phases,
                sort=resolved_sort,
            )
        )
        schools = _apply_saved_school_states(
            schools=schools,
            viewer_user_id=viewer_user_id,
            saved_school_state_resolver=self._saved_school_state_resolver,
        )
        return SchoolsSearchResponseDto(
            query=SchoolSearchQueryDto(
                postcode=center.postcode,
                radius_miles=resolved_radius,
                phases=resolved_phases,
                sort=resolved_sort,
            ),
            center=SearchCenterDto(lat=center.lat, lng=center.lng),
            schools=schools,
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


def _validate_phase_filters(phases: Sequence[str] | None) -> tuple[str, ...]:
    if phases is None:
        return ()

    normalized: dict[str, None] = {}
    for phase in phases:
        if not isinstance(phase, str):
            raise InvalidSchoolSearchParametersError(
                "phase filters must be primary and/or secondary"
            )
        candidate = phase.strip().lower()
        if candidate not in VALID_PHASE_FILTERS:
            raise InvalidSchoolSearchParametersError(
                "phase filters must be primary and/or secondary"
            )
        normalized.setdefault(candidate, None)

    return tuple(phase for phase in VALID_PHASE_FILTERS if phase in normalized)


def _validate_sort(sort: str | None, phase_filters: tuple[str, ...]) -> str:
    if sort is None:
        return DEFAULT_SORT
    if not isinstance(sort, str):
        raise InvalidSchoolSearchParametersError("sort must be closest, ofsted, or academic")

    normalized_sort = sort.strip().lower() or DEFAULT_SORT
    if normalized_sort not in VALID_SORTS:
        raise InvalidSchoolSearchParametersError("sort must be closest, ofsted, or academic")
    if normalized_sort == "academic" and len(phase_filters) != 1:
        raise InvalidSchoolSearchParametersError("academic sort requires a single phase filter")
    return normalized_sort


class SearchSchoolsByNameUseCase:
    def __init__(
        self,
        school_search_repository: SchoolSearchRepository,
        saved_school_state_resolver: SavedSchoolStateResolver | None = None,
    ) -> None:
        self._school_search_repository = school_search_repository
        self._saved_school_state_resolver = saved_school_state_resolver

    def execute(
        self,
        *,
        name: str,
        limit: int = DEFAULT_NAME_SEARCH_LIMIT,
        viewer_user_id: UUID | None = None,
    ) -> SchoolNameSearchResponseDto:
        stripped = name.strip()
        if len(stripped) < MIN_NAME_LENGTH:
            raise InvalidSchoolSearchParametersError("name must be at least 3 characters.")
        schools = tuple(
            self._school_search_repository.search_by_name(
                name=stripped,
                limit=limit,
            )
        )
        schools = _apply_saved_school_states(
            schools=schools,
            viewer_user_id=viewer_user_id,
            saved_school_state_resolver=self._saved_school_state_resolver,
        )
        return SchoolNameSearchResponseDto(schools=tuple(schools))


class MaterializeSchoolSearchSummariesUseCase:
    def __init__(
        self,
        school_search_summary_materializer: SchoolSearchSummaryMaterializer,
    ) -> None:
        self._school_search_summary_materializer = school_search_summary_materializer

    def execute(self) -> int:
        return self._school_search_summary_materializer.materialize_all_search_summaries()


def _apply_saved_school_states(
    *,
    schools,
    viewer_user_id,
    saved_school_state_resolver: SavedSchoolStateResolver | None,
):
    if len(schools) == 0:
        return schools
    if saved_school_state_resolver is None:
        default_state = (
            anonymous_saved_school_state()
            if viewer_user_id is None
            else SavedSchoolStateDto(
                status="not_saved",
                saved_at=None,
                capability_key=None,
                reason_code=None,
            )
        )
        return tuple(replace(school, saved_state=default_state) for school in schools)

    states = saved_school_state_resolver.execute(
        user_id=viewer_user_id,
        school_urns=tuple(school.urn for school in schools),
    )
    return tuple(
        replace(
            school,
            saved_state=states.get(school.urn, anonymous_saved_school_state()),
        )
        for school in schools
    )
