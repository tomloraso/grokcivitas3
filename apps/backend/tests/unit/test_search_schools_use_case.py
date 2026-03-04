from __future__ import annotations

from civitas.application.schools.errors import InvalidSchoolSearchParametersError
from civitas.application.schools.use_cases import (
    DEFAULT_RADIUS_MILES,
    SearchSchoolsByPostcodeUseCase,
)
from civitas.domain.schools.models import PostcodeCoordinates, SchoolSearchResult


class FakePostcodeResolver:
    def __init__(self, coordinates: PostcodeCoordinates) -> None:
        self._coordinates = coordinates
        self.received_postcodes: list[str] = []

    def resolve(self, postcode: str) -> PostcodeCoordinates:
        self.received_postcodes.append(postcode)
        return self._coordinates


class FakeSchoolSearchRepository:
    def __init__(self, results: list[SchoolSearchResult]) -> None:
        self._results = results
        self.search_requests: list[tuple[float, float, float]] = []

    def search_within_radius(
        self,
        *,
        center_lat: float,
        center_lng: float,
        radius_miles: float,
    ) -> list[SchoolSearchResult]:
        self.search_requests.append((center_lat, center_lng, radius_miles))
        return list(self._results)


def test_search_schools_uses_default_radius_and_normalized_postcode() -> None:
    resolver = FakePostcodeResolver(
        PostcodeCoordinates(
            postcode="SW1A 1AA",
            lat=51.501009,
            lng=-0.141588,
            lsoa_code="E01004736",
            lsoa="Westminster 018B",
            admin_district="Westminster",
        )
    )
    repository = FakeSchoolSearchRepository(results=[])
    use_case = SearchSchoolsByPostcodeUseCase(
        school_search_repository=repository,
        postcode_resolver=resolver,
    )

    result = use_case.execute(postcode=" sw1a1aa ")

    assert result.query.postcode == "SW1A 1AA"
    assert result.query.radius_miles == DEFAULT_RADIUS_MILES
    assert resolver.received_postcodes == ["SW1A 1AA"]
    assert repository.search_requests == [(51.501009, -0.141588, DEFAULT_RADIUS_MILES)]


def test_search_schools_rejects_invalid_radius() -> None:
    resolver = FakePostcodeResolver(
        PostcodeCoordinates(
            postcode="SW1A 1AA",
            lat=51.501009,
            lng=-0.141588,
            lsoa_code=None,
            lsoa=None,
            admin_district=None,
        )
    )
    repository = FakeSchoolSearchRepository(results=[])
    use_case = SearchSchoolsByPostcodeUseCase(
        school_search_repository=repository,
        postcode_resolver=resolver,
    )

    for radius in (0.0, -1.0, 25.1):
        try:
            use_case.execute(postcode="SW1A 1AA", radius_miles=radius)
        except InvalidSchoolSearchParametersError:
            continue
        raise AssertionError(
            f"Expected radius={radius} to raise InvalidSchoolSearchParametersError"
        )


def test_search_schools_returns_deterministic_distance_ordering() -> None:
    resolver = FakePostcodeResolver(
        PostcodeCoordinates(
            postcode="SW1A 1AA",
            lat=51.501009,
            lng=-0.141588,
            lsoa_code=None,
            lsoa=None,
            admin_district=None,
        )
    )
    repository = FakeSchoolSearchRepository(
        results=[
            SchoolSearchResult(
                urn="300003",
                name="Later By URN",
                school_type="Community school",
                phase="Primary",
                postcode="SW1A 1AA",
                lat=51.5000,
                lng=-0.1420,
                distance_miles=0.2,
            ),
            SchoolSearchResult(
                urn="300001",
                name="Nearest School",
                school_type="Community school",
                phase="Primary",
                postcode="SW1A 1AA",
                lat=51.5011,
                lng=-0.1416,
                distance_miles=0.1,
            ),
            SchoolSearchResult(
                urn="300002",
                name="Earlier By URN",
                school_type="Community school",
                phase="Primary",
                postcode="SW1A 1AA",
                lat=51.5001,
                lng=-0.1421,
                distance_miles=0.2,
            ),
        ]
    )
    use_case = SearchSchoolsByPostcodeUseCase(
        school_search_repository=repository,
        postcode_resolver=resolver,
    )

    result = use_case.execute(postcode="SW1A 1AA", radius_miles=5.0)

    assert [school.urn for school in result.schools] == ["300001", "300002", "300003"]
