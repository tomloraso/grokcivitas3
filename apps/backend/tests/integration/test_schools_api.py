from __future__ import annotations

from fastapi.testclient import TestClient

from civitas.api.dependencies import get_search_schools_by_postcode_use_case
from civitas.api.main import app
from civitas.application.schools.dto import (
    SchoolSearchQueryDto,
    SchoolsSearchResponseDto,
    SearchCenterDto,
)
from civitas.application.schools.errors import (
    InvalidSchoolSearchParametersError,
    PostcodeNotFoundError,
    PostcodeResolverUnavailableError,
)
from civitas.domain.schools.models import SchoolSearchResult

client = TestClient(app)


class FakeSearchSchoolsByPostcodeUseCase:
    def __init__(
        self, result: SchoolsSearchResponseDto | None = None, error: Exception | None = None
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[tuple[str, float | None]] = []

    def execute(
        self, *, postcode: str, radius_miles: float | None = None
    ) -> SchoolsSearchResponseDto:
        self.calls.append((postcode, radius_miles))
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError(
                "FakeSearchSchoolsByPostcodeUseCase configured without result or error"
            )
        return self._result


def setup_function() -> None:
    app.dependency_overrides.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_search_schools_returns_expected_contract() -> None:
    fake_use_case = FakeSearchSchoolsByPostcodeUseCase(
        result=SchoolsSearchResponseDto(
            query=SchoolSearchQueryDto(postcode="SW1A 1AA", radius_miles=5.0),
            center=SearchCenterDto(lat=51.501009, lng=-0.141588),
            schools=(
                SchoolSearchResult(
                    urn="123456",
                    name="Example Primary School",
                    school_type="Community school",
                    phase="Primary",
                    postcode="SW1A 1AA",
                    lat=51.5002,
                    lng=-0.1421,
                    distance_miles=0.09,
                ),
            ),
        )
    )
    app.dependency_overrides[get_search_schools_by_postcode_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools", params={"postcode": "sw1a1aa", "radius": "5"})

    assert response.status_code == 200
    assert response.json() == {
        "query": {
            "postcode": "SW1A 1AA",
            "radius_miles": 5.0,
        },
        "center": {"lat": 51.501009, "lng": -0.141588},
        "count": 1,
        "schools": [
            {
                "urn": "123456",
                "name": "Example Primary School",
                "type": "Community school",
                "phase": "Primary",
                "postcode": "SW1A 1AA",
                "lat": 51.5002,
                "lng": -0.1421,
                "distance_miles": 0.09,
            }
        ],
    }
    assert fake_use_case.calls == [("sw1a1aa", 5.0)]


def test_search_schools_returns_400_for_invalid_input() -> None:
    fake_use_case = FakeSearchSchoolsByPostcodeUseCase(
        error=InvalidSchoolSearchParametersError("radius must be between 0 and 25 miles")
    )
    app.dependency_overrides[get_search_schools_by_postcode_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools", params={"postcode": "SW1A1AA", "radius": "99"})

    assert response.status_code == 400
    assert response.json() == {"detail": "radius must be between 0 and 25 miles"}


def test_search_schools_returns_400_for_non_numeric_radius() -> None:
    fake_use_case = FakeSearchSchoolsByPostcodeUseCase(
        error=AssertionError("use case should not be called for invalid radius parsing")
    )
    app.dependency_overrides[get_search_schools_by_postcode_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools", params={"postcode": "SW1A 1AA", "radius": "abc"})

    assert response.status_code == 400
    assert response.json() == {"detail": "radius must be between 0 and 25 miles"}
    assert fake_use_case.calls == []


def test_search_schools_returns_400_when_postcode_is_missing() -> None:
    fake_use_case = FakeSearchSchoolsByPostcodeUseCase(
        error=AssertionError("use case should not be called when postcode is missing")
    )
    app.dependency_overrides[get_search_schools_by_postcode_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools")

    assert response.status_code == 400
    assert response.json() == {"detail": "postcode must be a valid UK postcode."}
    assert fake_use_case.calls == []


def test_search_schools_returns_404_for_missing_postcode() -> None:
    fake_use_case = FakeSearchSchoolsByPostcodeUseCase(error=PostcodeNotFoundError("ZZ99 9ZZ"))
    app.dependency_overrides[get_search_schools_by_postcode_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools", params={"postcode": "ZZ99 9ZZ"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Postcode 'ZZ99 9ZZ' was not found."}


def test_search_schools_returns_503_when_resolver_is_unavailable() -> None:
    fake_use_case = FakeSearchSchoolsByPostcodeUseCase(
        error=PostcodeResolverUnavailableError("Postcode resolver is unavailable.")
    )
    app.dependency_overrides[get_search_schools_by_postcode_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools", params={"postcode": "SW1A 1AA"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Postcode resolver is unavailable."}
