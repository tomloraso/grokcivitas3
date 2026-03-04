from __future__ import annotations

from civitas.application.schools.dto import SchoolNameSearchResponseDto
from civitas.application.schools.errors import InvalidSchoolSearchParametersError
from civitas.application.schools.use_cases import SearchSchoolsByNameUseCase
from civitas.domain.schools.models import SchoolSearchResult


class FakeSchoolSearchRepository:
    def __init__(self, results: list[SchoolSearchResult]) -> None:
        self._results = results
        self.name_queries: list[tuple[str, int]] = []

    def search_within_radius(
        self,
        *,
        center_lat: float,
        center_lng: float,
        radius_miles: float,
    ) -> list[SchoolSearchResult]:
        raise NotImplementedError("should not be called for name search")

    def search_by_name(self, *, name: str, limit: int) -> list[SchoolSearchResult]:
        self.name_queries.append((name, limit))
        return list(self._results)


def _make_school(urn: str, name: str, phase: str = "Primary") -> SchoolSearchResult:
    return SchoolSearchResult(
        urn=urn,
        name=name,
        school_type="Community school",
        phase=phase,
        postcode="SW1A 1AA",
        lat=51.5,
        lng=-0.14,
        distance_miles=0.0,
    )


def test_name_search_returns_matching_schools() -> None:
    repository = FakeSchoolSearchRepository(
        results=[
            _make_school("100001", "Springfield Primary"),
            _make_school("100002", "Springfield Academy"),
        ]
    )
    use_case = SearchSchoolsByNameUseCase(school_search_repository=repository)

    result = use_case.execute(name="Springfield")

    assert isinstance(result, SchoolNameSearchResponseDto)
    assert result.count == 2
    assert result.schools[0].name == "Springfield Primary"
    assert result.schools[1].name == "Springfield Academy"
    assert repository.name_queries == [("Springfield", 50)]


def test_name_search_respects_custom_limit() -> None:
    repository = FakeSchoolSearchRepository(results=[_make_school("100001", "Test School")])
    use_case = SearchSchoolsByNameUseCase(school_search_repository=repository)

    use_case.execute(name="Test", limit=10)

    assert repository.name_queries == [("Test", 10)]


def test_name_search_rejects_empty_name() -> None:
    repository = FakeSchoolSearchRepository(results=[])
    use_case = SearchSchoolsByNameUseCase(school_search_repository=repository)

    try:
        use_case.execute(name="")
    except InvalidSchoolSearchParametersError:
        pass
    else:
        raise AssertionError("Expected InvalidSchoolSearchParametersError for empty name")


def test_name_search_rejects_whitespace_only_name() -> None:
    repository = FakeSchoolSearchRepository(results=[])
    use_case = SearchSchoolsByNameUseCase(school_search_repository=repository)

    try:
        use_case.execute(name="   ")
    except InvalidSchoolSearchParametersError:
        pass
    else:
        raise AssertionError("Expected InvalidSchoolSearchParametersError for whitespace name")


def test_name_search_rejects_short_name() -> None:
    repository = FakeSchoolSearchRepository(results=[])
    use_case = SearchSchoolsByNameUseCase(school_search_repository=repository)

    try:
        use_case.execute(name="ab")
    except InvalidSchoolSearchParametersError:
        pass
    else:
        raise AssertionError("Expected InvalidSchoolSearchParametersError for name < 3 chars")


def test_name_search_returns_empty_when_no_matches() -> None:
    repository = FakeSchoolSearchRepository(results=[])
    use_case = SearchSchoolsByNameUseCase(school_search_repository=repository)

    result = use_case.execute(name="Nonexistent")

    assert result.count == 0
    assert result.schools == ()
