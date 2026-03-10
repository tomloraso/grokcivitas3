from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from civitas.api.dependencies import (
    get_current_session_use_case,
    get_search_schools_by_name_use_case,
)
from civitas.api.main import app
from civitas.application.favourites.dto import SavedSchoolStateDto
from civitas.application.identity.dto import CurrentSessionDto, SessionUserDto
from civitas.application.schools.dto import (
    SchoolNameSearchItemDto,
    SchoolNameSearchResponseDto,
)
from civitas.application.schools.errors import InvalidSchoolSearchParametersError

client = TestClient(app)


class FakeSearchSchoolsByNameUseCase:
    def __init__(
        self, result: SchoolNameSearchResponseDto | None = None, error: Exception | None = None
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[tuple[str, int | None, UUID | None]] = []

    def execute(
        self,
        *,
        name: str,
        limit: int = 50,
        viewer_user_id: UUID | None = None,
    ) -> SchoolNameSearchResponseDto:
        self.calls.append((name, limit, viewer_user_id))
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError(
                "FakeSearchSchoolsByNameUseCase configured without result or error"
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


def test_search_by_name_returns_expected_contract() -> None:
    fake_use_case = FakeSearchSchoolsByNameUseCase(
        result=SchoolNameSearchResponseDto(
            schools=(
                SchoolNameSearchItemDto(
                    urn="123456",
                    name="Springfield Primary School",
                    school_type="Community school",
                    phase="Primary",
                    postcode="SW1A 1AA",
                    lat=51.5002,
                    lng=-0.1421,
                    distance_miles=0.0,
                    saved_state=SavedSchoolStateDto(
                        status="requires_auth",
                        saved_at=None,
                        capability_key=None,
                        reason_code="anonymous_user",
                    ),
                ),
                SchoolNameSearchItemDto(
                    urn="123457",
                    name="Springfield Academy",
                    school_type="Academy converter",
                    phase="Secondary",
                    postcode="SW1A 2BB",
                    lat=51.5010,
                    lng=-0.1430,
                    distance_miles=0.0,
                    saved_state=SavedSchoolStateDto(
                        status="saved",
                        saved_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
                        capability_key=None,
                        reason_code=None,
                    ),
                ),
            ),
        )
    )
    app.dependency_overrides[get_search_schools_by_name_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/search", params={"name": "Springfield"})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert len(body["schools"]) == 2
    assert body["schools"][0]["urn"] == "123456"
    assert body["schools"][0]["name"] == "Springfield Primary School"
    assert body["schools"][0]["saved_state"] == {
        "status": "requires_auth",
        "saved_at": None,
        "capability_key": None,
        "reason_code": "anonymous_user",
    }
    assert body["schools"][1]["urn"] == "123457"
    assert body["schools"][1]["saved_state"] == {
        "status": "saved",
        "saved_at": "2026-03-10T09:00:00Z",
        "capability_key": None,
        "reason_code": None,
    }
    assert "query" not in body
    assert "center" not in body
    assert fake_use_case.calls == [("Springfield", 50, None)]


def test_search_by_name_returns_422_for_empty_name() -> None:
    fake_use_case = FakeSearchSchoolsByNameUseCase(
        error=InvalidSchoolSearchParametersError("name must be at least 3 characters.")
    )
    app.dependency_overrides[get_search_schools_by_name_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/search", params={"name": ""})

    assert response.status_code == 422  # FastAPI min_length validation


def test_search_by_name_returns_400_when_name_is_missing() -> None:
    fake_use_case = FakeSearchSchoolsByNameUseCase(
        error=AssertionError("use case should not be called when name is missing")
    )
    app.dependency_overrides[get_search_schools_by_name_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/search")

    assert response.status_code == 422  # FastAPI missing required query param


def test_search_by_name_returns_empty_list_when_no_matches() -> None:
    fake_use_case = FakeSearchSchoolsByNameUseCase(result=SchoolNameSearchResponseDto(schools=()))
    app.dependency_overrides[get_search_schools_by_name_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/search", params={"name": "Nonexistent"})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["schools"] == []


def test_search_by_name_passes_authenticated_viewer_to_use_case() -> None:
    user = SessionUserDto(
        id=UUID("a32d5bf0-0ec5-4dc9-bd40-636264a6fb96"),
        email="viewer@example.com",
    )
    fake_use_case = FakeSearchSchoolsByNameUseCase(result=SchoolNameSearchResponseDto(schools=()))
    app.dependency_overrides[get_current_session_use_case] = lambda: (
        FakeAuthenticatedSessionUseCase(user)
    )
    app.dependency_overrides[get_search_schools_by_name_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/schools/search", params={"name": "Springfield"})

    assert response.status_code == 200
    assert fake_use_case.calls == [("Springfield", 50, user.id)]
