from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from civitas.api.dependencies import (
    get_auth_allowed_origins,
    get_list_saved_schools_use_case,
    get_remove_saved_school_use_case,
    get_save_school_use_case,
    get_session_cookie_settings,
    require_authenticated_session,
)
from civitas.api.main import app
from civitas.api.session_cookies import SessionCookieSettings
from civitas.application.access.dto import SectionAccessDto
from civitas.application.favourites.dto import (
    AccountFavouriteSchoolDto,
    AccountFavouritesResponseDto,
    PostcodeSchoolSearchAcademicMetricDto,
    PostcodeSchoolSearchLatestOfstedDto,
    SavedSchoolStateDto,
)
from civitas.application.identity.dto import SessionUserDto

client = TestClient(app)


class FakeListSavedSchoolsUseCase:
    def __init__(self, result: AccountFavouritesResponseDto) -> None:
        self._result = result
        self.calls: list[UUID] = []

    def execute(self, *, user_id: UUID) -> AccountFavouritesResponseDto:
        self.calls.append(user_id)
        return self._result


class FakeSaveSchoolUseCase:
    def __init__(self, result: SavedSchoolStateDto) -> None:
        self._result = result
        self.calls: list[tuple[UUID, str]] = []

    def execute(self, *, user_id: UUID, school_urn: str) -> SavedSchoolStateDto:
        self.calls.append((user_id, school_urn))
        return self._result


class FakeRemoveSavedSchoolUseCase:
    def __init__(self, result: SavedSchoolStateDto) -> None:
        self._result = result
        self.calls: list[tuple[UUID, str]] = []

    def execute(self, *, user_id: UUID, school_urn: str) -> SavedSchoolStateDto:
        self.calls.append((user_id, school_urn))
        return self._result


def setup_function() -> None:
    app.dependency_overrides.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_get_account_favourites_returns_saved_library_rows() -> None:
    user = SessionUserDto(
        id=UUID("a32d5bf0-0ec5-4dc9-bd40-636264a6fb96"),
        email="viewer@example.com",
    )
    fake_use_case = FakeListSavedSchoolsUseCase(
        AccountFavouritesResponseDto(
            access=SectionAccessDto(
                state="available",
                capability_key=None,
                reason_code=None,
                product_codes=(),
                requires_auth=False,
                requires_purchase=False,
            ),
            schools=(
                AccountFavouriteSchoolDto(
                    urn="123456",
                    name="Example School",
                    school_type="Community school",
                    phase="Primary",
                    postcode="SW1A 1AA",
                    pupil_count=320,
                    latest_ofsted=PostcodeSchoolSearchLatestOfstedDto(
                        label="Good",
                        sort_rank=2,
                        availability="published",
                    ),
                    academic_metric=PostcodeSchoolSearchAcademicMetricDto(
                        metric_key="ks2_combined_expected_pct",
                        label="KS2 expected standard",
                        display_value="68%",
                        sort_value=68.0,
                        availability="published",
                    ),
                    saved_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
                ),
            ),
        )
    )
    app.dependency_overrides[require_authenticated_session] = lambda: user
    app.dependency_overrides[get_list_saved_schools_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/account/favourites")

    assert response.status_code == 200
    assert response.json() == {
        "access": {
            "state": "available",
            "capability_key": None,
            "reason_code": None,
            "product_codes": [],
            "requires_auth": False,
            "requires_purchase": False,
            "school_name": None,
        },
        "count": 1,
        "schools": [
            {
                "urn": "123456",
                "name": "Example School",
                "type": "Community school",
                "phase": "Primary",
                "postcode": "SW1A 1AA",
                "pupil_count": 320,
                "latest_ofsted": {
                    "label": "Good",
                    "sort_rank": 2,
                    "availability": "published",
                },
                "academic_metric": {
                    "metric_key": "ks2_combined_expected_pct",
                    "label": "KS2 expected standard",
                    "display_value": "68%",
                    "sort_value": 68.0,
                    "availability": "published",
                },
                "saved_at": "2026-03-10T09:00:00Z",
            }
        ],
    }
    assert fake_use_case.calls == [user.id]


def test_put_account_favourite_returns_saved_state() -> None:
    user = SessionUserDto(
        id=UUID("a32d5bf0-0ec5-4dc9-bd40-636264a6fb96"),
        email="viewer@example.com",
    )
    fake_use_case = FakeSaveSchoolUseCase(
        SavedSchoolStateDto(
            status="saved",
            saved_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
            capability_key=None,
            reason_code=None,
        )
    )
    app.dependency_overrides[require_authenticated_session] = lambda: user
    app.dependency_overrides[get_save_school_use_case] = lambda: fake_use_case

    response = client.put("/api/v1/account/favourites/123456")

    assert response.status_code == 200
    assert response.json() == {
        "status": "saved",
        "saved_at": "2026-03-10T09:00:00Z",
        "capability_key": None,
        "reason_code": None,
    }
    assert fake_use_case.calls == [(user.id, "123456")]


def test_put_account_favourite_rejects_untrusted_origin_when_cookie_is_present() -> None:
    user = SessionUserDto(
        id=UUID("a32d5bf0-0ec5-4dc9-bd40-636264a6fb96"),
        email="viewer@example.com",
    )
    fake_use_case = FakeSaveSchoolUseCase(
        SavedSchoolStateDto(
            status="saved",
            saved_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
            capability_key=None,
            reason_code=None,
        )
    )
    app.dependency_overrides[require_authenticated_session] = lambda: user
    app.dependency_overrides[get_save_school_use_case] = lambda: fake_use_case
    app.dependency_overrides[get_session_cookie_settings] = lambda: SessionCookieSettings(
        name="civitas_session",
        secure=False,
        samesite="lax",
    )
    app.dependency_overrides[get_auth_allowed_origins] = lambda: ("https://allowed.example",)

    response = client.put(
        "/api/v1/account/favourites/123456",
        cookies={"civitas_session": "session-token"},
        headers={"origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "origin not allowed"}
    assert fake_use_case.calls == []


def test_delete_account_favourite_returns_not_saved_state() -> None:
    user = SessionUserDto(
        id=UUID("a32d5bf0-0ec5-4dc9-bd40-636264a6fb96"),
        email="viewer@example.com",
    )
    fake_use_case = FakeRemoveSavedSchoolUseCase(
        SavedSchoolStateDto(
            status="not_saved",
            saved_at=None,
            capability_key=None,
            reason_code=None,
        )
    )
    app.dependency_overrides[require_authenticated_session] = lambda: user
    app.dependency_overrides[get_remove_saved_school_use_case] = lambda: fake_use_case

    response = client.delete("/api/v1/account/favourites/123456")

    assert response.status_code == 200
    assert response.json() == {
        "status": "not_saved",
        "saved_at": None,
        "capability_key": None,
        "reason_code": None,
    }
    assert fake_use_case.calls == [(user.id, "123456")]
