from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from civitas.api.dependencies import (
    get_auth_allowed_origins,
    get_complete_auth_callback_use_case,
    get_current_session_use_case,
    get_sign_out_use_case,
    get_start_sign_in_use_case,
)
from civitas.api.main import app
from civitas.application.identity.dto import (
    CompleteAuthCallbackResultDto,
    CurrentSessionDto,
    SessionUserDto,
    StartSignInResultDto,
)
from civitas.application.identity.errors import (
    IdentityProviderUnavailableError,
    InvalidAuthCallbackError,
)

client = TestClient(app)


class FakeStartSignInUseCase:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None, str]] = []

    def execute(
        self, *, email: str, return_to: str | None, callback_url: str
    ) -> StartSignInResultDto:
        self.calls.append((email, return_to, callback_url))
        return StartSignInResultDto(
            redirect_url="/api/v1/auth/callback?state=state-1&ticket=valid-ticket"
        )


class FakeCurrentSessionUseCase:
    def __init__(self, result: CurrentSessionDto) -> None:
        self._result = result
        self.calls: list[str | None] = []

    def execute(self, *, session_token: str | None) -> CurrentSessionDto:
        self.calls.append(session_token)
        return self._result


class FakeCompleteAuthCallbackUseCase:
    def __init__(
        self,
        result: CompleteAuthCallbackResultDto | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[tuple[dict[str, str], str]] = []

    def execute(
        self,
        *,
        callback_params: dict[str, str],
        callback_url: str,
    ) -> CompleteAuthCallbackResultDto:
        self.calls.append((callback_params, callback_url))
        if self._error is not None:
            raise self._error
        if self._result is None:
            raise AssertionError("FakeCompleteAuthCallbackUseCase missing result")
        return self._result


class FakeSignOutUseCase:
    def __init__(self, result: CurrentSessionDto) -> None:
        self._result = result
        self.calls: list[str | None] = []

    def execute(self, *, session_token: str | None) -> CurrentSessionDto:
        self.calls.append(session_token)
        return self._result


def setup_function() -> None:
    app.dependency_overrides.clear()
    client.cookies.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()
    client.cookies.clear()


def test_get_session_returns_anonymous_contract() -> None:
    fake_use_case = FakeCurrentSessionUseCase(CurrentSessionDto.anonymous(reason="missing"))
    app.dependency_overrides[get_current_session_use_case] = lambda: fake_use_case

    response = client.get("/api/v1/session")

    assert response.status_code == 200
    assert response.json() == {
        "state": "anonymous",
        "user": None,
        "expires_at": None,
        "anonymous_reason": "missing",
    }
    assert fake_use_case.calls == [None]


def test_start_sign_in_returns_redirect_url() -> None:
    fake_use_case = FakeStartSignInUseCase()
    app.dependency_overrides[get_start_sign_in_use_case] = lambda: fake_use_case

    response = client.post(
        "/api/v1/auth/start",
        json={"email": "person@example.com", "return_to": "/compare"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "redirect_url": "/api/v1/auth/callback?state=state-1&ticket=valid-ticket"
    }
    assert fake_use_case.calls == [
        (
            "person@example.com",
            "/compare",
            "http://testserver/api/v1/auth/callback",
        )
    ]


def test_start_sign_in_returns_503_when_provider_is_unavailable() -> None:
    class UnavailableStartSignInUseCase:
        def execute(
            self,
            *,
            email: str,
            return_to: str | None,
            callback_url: str,
        ) -> StartSignInResultDto:
            raise IdentityProviderUnavailableError("provider unavailable")

    app.dependency_overrides[get_start_sign_in_use_case] = lambda: UnavailableStartSignInUseCase()

    response = client.post(
        "/api/v1/auth/start",
        json={"email": "person@example.com", "return_to": "/compare"},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "provider unavailable"}


def test_auth_callback_sets_cookie_and_redirects_to_return_to() -> None:
    fake_use_case = FakeCompleteAuthCallbackUseCase(
        result=CompleteAuthCallbackResultDto(
            return_to="/compare",
            session_token="session-token",
            expires_at=datetime(2026, 3, 21, 10, 0, tzinfo=timezone.utc),
            user=SessionUserDto(
                id=UUID("a32d5bf0-0ec5-4dc9-bd40-636264a6fb96"),
                email="person@example.com",
            ),
        )
    )
    app.dependency_overrides[get_complete_auth_callback_use_case] = lambda: fake_use_case

    response = client.get(
        "/api/v1/auth/callback?state=state-1&ticket=valid-ticket",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/compare"
    assert "civitas_session=" in response.headers["set-cookie"]
    assert fake_use_case.calls == [
        (
            {"state": "state-1", "ticket": "valid-ticket"},
            "http://testserver/api/v1/auth/callback",
        )
    ]


def test_auth_callback_forwards_auth0_code_callback_params() -> None:
    fake_use_case = FakeCompleteAuthCallbackUseCase(
        result=CompleteAuthCallbackResultDto(
            return_to="/compare",
            session_token="session-token",
            expires_at=datetime(2026, 3, 21, 10, 0, tzinfo=timezone.utc),
            user=SessionUserDto(
                id=UUID("a32d5bf0-0ec5-4dc9-bd40-636264a6fb96"),
                email="person@example.com",
            ),
        )
    )
    app.dependency_overrides[get_complete_auth_callback_use_case] = lambda: fake_use_case

    response = client.get(
        "/api/v1/auth/callback?state=state-1&code=authorization-code",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/compare"
    assert fake_use_case.calls == [
        (
            {"state": "state-1", "code": "authorization-code"},
            "http://testserver/api/v1/auth/callback",
        )
    ]


def test_auth_callback_redirects_back_to_sign_in_on_failure() -> None:
    fake_use_case = FakeCompleteAuthCallbackUseCase(
        error=InvalidAuthCallbackError("invalid auth state")
    )
    app.dependency_overrides[get_complete_auth_callback_use_case] = lambda: fake_use_case

    response = client.get(
        "/api/v1/auth/callback?state=bad&ticket=invalid",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/sign-in?error=invalid_state"


def test_auth_callback_redirects_with_unverified_email_error_code() -> None:
    fake_use_case = FakeCompleteAuthCallbackUseCase(
        error=InvalidAuthCallbackError("email address must be verified")
    )
    app.dependency_overrides[get_complete_auth_callback_use_case] = lambda: fake_use_case

    response = client.get(
        "/api/v1/auth/callback?state=state-1&ticket=valid-ticket",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/sign-in?error=unverified_email"


def test_auth_callback_redirects_with_callback_failed_when_provider_is_unavailable() -> None:
    fake_use_case = FakeCompleteAuthCallbackUseCase(
        error=IdentityProviderUnavailableError("provider unavailable")
    )
    app.dependency_overrides[get_complete_auth_callback_use_case] = lambda: fake_use_case

    response = client.get(
        "/api/v1/auth/callback?state=state-1&ticket=valid-ticket",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/sign-in?error=callback_failed"


def test_get_session_clears_cookie_for_invalid_session_token() -> None:
    fake_use_case = FakeCurrentSessionUseCase(CurrentSessionDto.anonymous(reason="invalid"))
    app.dependency_overrides[get_current_session_use_case] = lambda: fake_use_case

    client.cookies.set("civitas_session", "bad-token")
    response = client.get("/api/v1/session")

    assert response.status_code == 200
    assert response.json()["anonymous_reason"] == "invalid"
    assert "civitas_session=" in response.headers["set-cookie"]
    assert fake_use_case.calls == ["bad-token"]


def test_sign_out_clears_cookie_and_returns_anonymous_state() -> None:
    fake_use_case = FakeSignOutUseCase(CurrentSessionDto.anonymous(reason="signed_out"))
    app.dependency_overrides[get_auth_allowed_origins] = lambda: ("http://testserver",)
    app.dependency_overrides[get_sign_out_use_case] = lambda: fake_use_case

    client.cookies.set("civitas_session", "session-token")
    response = client.post(
        "/api/v1/auth/signout",
        headers={"origin": "http://testserver"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "state": "anonymous",
        "user": None,
        "expires_at": None,
        "anonymous_reason": "signed_out",
    }
    assert "civitas_session=" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert fake_use_case.calls == ["session-token"]


def test_sign_out_rejects_untrusted_origin_when_session_cookie_present() -> None:
    fake_use_case = FakeSignOutUseCase(CurrentSessionDto.anonymous(reason="signed_out"))
    app.dependency_overrides[get_auth_allowed_origins] = lambda: ("http://testserver",)
    app.dependency_overrides[get_sign_out_use_case] = lambda: fake_use_case

    client.cookies.set("civitas_session", "session-token")
    response = client.post(
        "/api/v1/auth/signout",
        headers={"origin": "https://malicious.example.test"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "origin not allowed"}
    assert fake_use_case.calls == []
