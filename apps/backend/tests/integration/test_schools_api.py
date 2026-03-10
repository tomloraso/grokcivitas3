from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from civitas.api.dependencies import (
    get_current_session_use_case,
    get_search_schools_by_postcode_use_case,
)
from civitas.api.main import app
from civitas.application.favourites.dto import SavedSchoolStateDto
from civitas.application.identity.dto import CurrentSessionDto, SessionUserDto
from civitas.application.schools.dto import (
    PostcodeSchoolSearchAcademicMetricDto,
    PostcodeSchoolSearchItemDto,
    PostcodeSchoolSearchLatestOfstedDto,
    SchoolSearchQueryDto,
    SchoolsSearchResponseDto,
    SearchCenterDto,
)
from civitas.application.schools.errors import (
    InvalidSchoolSearchParametersError,
    PostcodeNotFoundError,
    PostcodeResolverUnavailableError,
)

client = TestClient(app)


class FakeSearchSchoolsByPostcodeUseCase:
    def __init__(
        self, result: SchoolsSearchResponseDto | None = None, error: Exception | None = None
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[
            tuple[str, float | None, tuple[str, ...] | None, str | None, UUID | None]
        ] = []

    def execute(
        self,
        *,
        postcode: str,
        radius_miles: float | None = None,
        phases: tuple[str, ...] | None = None,
        sort: str | None = None,
        viewer_user_id: UUID | None = None,
    ) -> SchoolsSearchResponseDto:
        self.calls.append((postcode, radius_miles, phases, sort, viewer_user_id))
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError(
                "FakeSearchSchoolsByPostcodeUseCase configured without result or error"
            )
        return self._result


class FakeAnonymousSessionUseCase:
    def execute(self, *, session_token: str | None) -> CurrentSessionDto:
        return CurrentSessionDto.anonymous(reason="missing")


class FakeAuthenticatedSessionUseCase:
    def __init__(self, user: SessionUserDto) -> None:
        self._user = user

    def execute(self, *, session_token: str | None) -> CurrentSessionDto:
        return CurrentSessionDto.authenticated(
            user=self._user,
            expires_at=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
        )


def setup_function() -> None:
    app.dependency_overrides.clear()
    app.dependency_overrides[get_current_session_use_case] = lambda: FakeAnonymousSessionUseCase()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_search_schools_returns_expected_contract() -> None:
    fake_use_case = FakeSearchSchoolsByPostcodeUseCase(
        result=SchoolsSearchResponseDto(
            query=SchoolSearchQueryDto(
                postcode="SW1A 1AA",
                radius_miles=5.0,
                phases=("secondary",),
                sort="ofsted",
            ),
            center=SearchCenterDto(lat=51.501009, lng=-0.141588),
            schools=(
                PostcodeSchoolSearchItemDto(
                    urn="123456",
                    name="Example Primary School",
                    school_type="Community school",
                    phase="Secondary",
                    postcode="SW1A 1AA",
                    lat=51.5002,
                    lng=-0.1421,
                    distance_miles=0.09,
                    pupil_count=812,
                    latest_ofsted=PostcodeSchoolSearchLatestOfstedDto(
                        label="Outstanding",
                        sort_rank=1,
                        availability="published",
                    ),
                    academic_metric=PostcodeSchoolSearchAcademicMetricDto(
                        metric_key="progress8_average",
                        label="Progress 8",
                        display_value="0.42",
                        sort_value=0.42,
                        availability="published",
                    ),
                    saved_state=SavedSchoolStateDto(
                        status="requires_auth",
                        saved_at=None,
                        capability_key=None,
                        reason_code="anonymous_user",
                    ),
                ),
            ),
        )
    )
    app.dependency_overrides[get_search_schools_by_postcode_use_case] = lambda: fake_use_case

    response = client.get(
        "/api/v1/schools",
        params=[
            ("postcode", "sw1a1aa"),
            ("radius", "5"),
            ("phase", "secondary"),
            ("sort", "ofsted"),
        ],
    )

    assert response.status_code == 200
    assert response.json() == {
        "query": {
            "postcode": "SW1A 1AA",
            "radius_miles": 5.0,
            "phases": ["secondary"],
            "sort": "ofsted",
        },
        "center": {"lat": 51.501009, "lng": -0.141588},
        "count": 1,
        "schools": [
            {
                "urn": "123456",
                "name": "Example Primary School",
                "type": "Community school",
                "phase": "Secondary",
                "postcode": "SW1A 1AA",
                "lat": 51.5002,
                "lng": -0.1421,
                "distance_miles": 0.09,
                "pupil_count": 812,
                "latest_ofsted": {
                    "label": "Outstanding",
                    "sort_rank": 1,
                    "availability": "published",
                },
                "academic_metric": {
                    "metric_key": "progress8_average",
                    "label": "Progress 8",
                    "display_value": "0.42",
                    "sort_value": 0.42,
                    "availability": "published",
                },
                "saved_state": {
                    "status": "requires_auth",
                    "saved_at": None,
                    "capability_key": None,
                    "reason_code": "anonymous_user",
                },
            }
        ],
    }
    assert fake_use_case.calls == [("sw1a1aa", 5.0, ("secondary",), "ofsted", None)]


def test_search_schools_returns_400_for_invalid_input() -> None:
    fake_use_case = FakeSearchSchoolsByPostcodeUseCase(
        error=InvalidSchoolSearchParametersError("academic sort requires a single phase filter")
    )
    app.dependency_overrides[get_search_schools_by_postcode_use_case] = lambda: fake_use_case

    response = client.get(
        "/api/v1/schools",
        params=[
            ("postcode", "SW1A1AA"),
            ("phase", "primary"),
            ("phase", "secondary"),
            ("sort", "academic"),
        ],
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "academic sort requires a single phase filter"}


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


def test_search_schools_passes_authenticated_viewer_to_use_case() -> None:
    user = SessionUserDto(
        id=UUID("a32d5bf0-0ec5-4dc9-bd40-636264a6fb96"),
        email="viewer@example.com",
    )
    fake_use_case = FakeSearchSchoolsByPostcodeUseCase(
        result=SchoolsSearchResponseDto(
            query=SchoolSearchQueryDto(
                postcode="SW1A 1AA",
                radius_miles=5.0,
                phases=(),
                sort="closest",
            ),
            center=SearchCenterDto(lat=51.501009, lng=-0.141588),
            schools=(),
        )
    )
    app.dependency_overrides[get_current_session_use_case] = lambda: (
        FakeAuthenticatedSessionUseCase(user)
    )
    app.dependency_overrides[get_search_schools_by_postcode_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools", params={"postcode": "SW1A 1AA"})

    assert response.status_code == 200
    assert fake_use_case.calls == [("SW1A 1AA", None, None, None, user.id)]
