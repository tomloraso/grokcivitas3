from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from civitas.application.identity.dto import (
    AuthFlowStateDto,
    AuthProviderStartParamsDto,
    CompleteAuthCallbackResultDto,
    IdentityProviderUserDto,
)
from civitas.application.identity.errors import InvalidAuthCallbackError
from civitas.application.identity.use_cases import (
    CompleteAuthCallbackUseCase,
    GetCurrentSessionUseCase,
    SignOutUseCase,
    StartSignInUseCase,
)
from civitas.domain.identity.models import AppSession, AuthAttempt, AuthIdentity, UserAccount
from civitas.domain.identity.services import derive_pkce_code_challenge


class FakeIdentityProvider:
    def __init__(self, resolved_user: IdentityProviderUserDto | None = None) -> None:
        self._resolved_user = resolved_user or IdentityProviderUserDto(
            provider_name="development",
            provider_subject="person@example.com",
            email="person@example.com",
            email_verified=True,
        )
        self.start_calls: list[AuthProviderStartParamsDto] = []
        self.complete_calls: list[tuple[Mapping[str, str], str, str | None]] = []

    def start_sign_in(
        self,
        *,
        email: str,
        state: str,
        callback_url: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> str:
        self.start_calls.append(
            AuthProviderStartParamsDto(
                email=email,
                state=state,
                callback_url=callback_url,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
            )
        )
        return f"{callback_url}?state={state}&ticket=valid-ticket"

    def complete_sign_in(
        self,
        *,
        callback_params: Mapping[str, str],
        callback_url: str,
        code_verifier: str | None = None,
    ) -> IdentityProviderUserDto:
        self.complete_calls.append((callback_params, callback_url, code_verifier))
        if callback_params.get("ticket") != "valid-ticket":
            raise InvalidAuthCallbackError("provider callback could not be verified")
        return self._resolved_user


class FakeAuthFlowStateCodec:
    def __init__(self) -> None:
        self._states: dict[str, AuthFlowStateDto] = {}

    def issue(self, *, attempt_id: str) -> str:
        state = f"state-{len(self._states) + 1}"
        self._states[state] = AuthFlowStateDto(attempt_id=attempt_id)
        return state

    def read(self, *, state: str) -> AuthFlowStateDto:
        try:
            return self._states[state]
        except KeyError as exc:
            raise InvalidAuthCallbackError("invalid auth state") from exc


class FakeAuthAttemptRepository:
    def __init__(self) -> None:
        self.attempts: dict[str, AuthAttempt] = {}

    def add(self, attempt: AuthAttempt) -> AuthAttempt:
        self.attempts[attempt.id] = attempt
        return attempt

    def consume(self, *, attempt_id: str, now: datetime) -> AuthAttempt | None:
        attempt = self.attempts.get(attempt_id)
        if attempt is None or attempt.consumed_at is not None or attempt.is_expired(at=now):
            return None

        consumed_attempt = AuthAttempt(
            id=attempt.id,
            return_to=attempt.return_to,
            code_verifier=attempt.code_verifier,
            issued_at=attempt.issued_at,
            expires_at=attempt.expires_at,
            consumed_at=now,
        )
        self.attempts[attempt_id] = consumed_attempt
        return consumed_attempt


class FakeUserRepository:
    def __init__(self) -> None:
        self.users_by_id: dict[UUID, UserAccount] = {}
        self.users_by_email: dict[str, UserAccount] = {}
        self.identity_to_user_id: dict[tuple[str, str], UUID] = {}
        self.identities: dict[tuple[str, str], AuthIdentity] = {}

    def get_by_id(self, *, user_id: UUID) -> UserAccount | None:
        return self.users_by_id.get(user_id)

    def get_by_email(self, *, email: str) -> UserAccount | None:
        return self.users_by_email.get(email)

    def get_by_auth_identity(
        self, *, provider_name: str, provider_subject: str
    ) -> UserAccount | None:
        user_id = self.identity_to_user_id.get((provider_name, provider_subject))
        if user_id is None:
            return None
        return self.users_by_id.get(user_id)

    def add_user(self, user: UserAccount) -> UserAccount:
        self.users_by_id[user.id] = user
        self.users_by_email[user.email] = user
        return user

    def upsert_auth_identity(self, identity: AuthIdentity) -> AuthIdentity:
        self.identities[(identity.provider_name, identity.provider_subject)] = identity
        self.identity_to_user_id[(identity.provider_name, identity.provider_subject)] = (
            identity.user_id
        )
        return identity

    def update_user_last_sign_in(self, *, user_id: UUID, signed_in_at: datetime) -> None:
        user = self.users_by_id[user_id]
        updated = UserAccount(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
            last_sign_in_at=signed_in_at,
        )
        self.users_by_id[user_id] = updated
        self.users_by_email[user.email] = updated


class FakeSessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[str, AppSession] = {}

    def add(self, session: AppSession) -> AppSession:
        self.sessions[session.token] = session
        return session

    def get_by_token(self, *, token: str) -> AppSession | None:
        return self.sessions.get(token)

    def revoke(self, *, token: str, revoked_at: datetime, reason: str) -> AppSession | None:
        session = self.sessions.get(token)
        if session is None:
            return None
        updated = AppSession(
            token=session.token,
            user_id=session.user_id,
            issued_at=session.issued_at,
            last_seen_at=session.last_seen_at,
            expires_at=session.expires_at,
            revoked_at=revoked_at,
            revoke_reason=reason,
        )
        self.sessions[token] = updated
        return updated

    def touch(self, *, token: str, last_seen_at: datetime) -> None:
        session = self.sessions[token]
        self.sessions[token] = AppSession(
            token=session.token,
            user_id=session.user_id,
            issued_at=session.issued_at,
            last_seen_at=last_seen_at,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
            revoke_reason=session.revoke_reason,
        )


def test_start_sign_in_normalizes_email_and_sanitizes_return_to() -> None:
    provider = FakeIdentityProvider()
    auth_state_codec = FakeAuthFlowStateCodec()
    auth_attempt_repository = FakeAuthAttemptRepository()
    use_case = StartSignInUseCase(
        identity_provider=provider,
        auth_flow_state_codec=auth_state_codec,
        auth_attempt_repository=auth_attempt_repository,
        auth_attempt_ttl=timedelta(minutes=15),
    )

    result = use_case.execute(
        email=" Person@example.com ",
        return_to="https://malicious.example.test/phish",
        callback_url="http://testserver/api/v1/auth/callback",
    )

    assert result.redirect_url == (
        "http://testserver/api/v1/auth/callback?state=state-1&ticket=valid-ticket"
    )
    assert len(auth_attempt_repository.attempts) == 1
    attempt = next(iter(auth_attempt_repository.attempts.values()))
    assert attempt.return_to == "/"
    assert provider.start_calls == [
        AuthProviderStartParamsDto(
            email="person@example.com",
            state="state-1",
            callback_url="http://testserver/api/v1/auth/callback",
            code_challenge=derive_pkce_code_challenge(attempt.code_verifier),
            code_challenge_method="S256",
        )
    ]
    assert auth_state_codec.read(state="state-1").attempt_id == attempt.id


def test_complete_auth_callback_creates_user_identity_and_session() -> None:
    fixed_now = datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc)
    provider = FakeIdentityProvider()
    auth_state_codec = FakeAuthFlowStateCodec()
    auth_attempt_repository = FakeAuthAttemptRepository()
    attempt = auth_attempt_repository.add(
        AuthAttempt.create(
            return_to="/compare",
            code_verifier="pkce-verifier-1",
            ttl=timedelta(minutes=15),
            issued_at=fixed_now - timedelta(minutes=1),
        )
    )
    state = auth_state_codec.issue(attempt_id=attempt.id)
    user_repository = FakeUserRepository()
    session_repository = FakeSessionRepository()
    use_case = CompleteAuthCallbackUseCase(
        identity_provider=provider,
        auth_flow_state_codec=auth_state_codec,
        auth_attempt_repository=auth_attempt_repository,
        user_repository=user_repository,
        session_repository=session_repository,
        session_ttl=timedelta(days=14),
        clock=lambda: fixed_now,
    )

    result = use_case.execute(
        callback_params={"state": state, "ticket": "valid-ticket"},
        callback_url="http://testserver/api/v1/auth/callback",
    )

    assert isinstance(result, CompleteAuthCallbackResultDto)
    assert result.return_to == "/compare"
    assert result.user.email == "person@example.com"
    assert result.expires_at == fixed_now + timedelta(days=14)
    assert result.session_token in session_repository.sessions
    stored_session = session_repository.sessions[result.session_token]
    assert stored_session.user_id == result.user.id
    assert stored_session.issued_at == fixed_now
    assert user_repository.get_by_email(email="person@example.com") is not None
    assert provider.complete_calls == [
        (
            {"state": state, "ticket": "valid-ticket"},
            "http://testserver/api/v1/auth/callback",
            "pkce-verifier-1",
        )
    ]
    assert (
        user_repository.get_by_auth_identity(
            provider_name="development",
            provider_subject="person@example.com",
        )
        is not None
    )


def test_complete_auth_callback_links_existing_user_when_email_is_verified() -> None:
    fixed_now = datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc)
    provider = FakeIdentityProvider(
        resolved_user=IdentityProviderUserDto(
            provider_name="development",
            provider_subject="person@example.com",
            email="person@example.com",
            email_verified=True,
        )
    )
    auth_state_codec = FakeAuthFlowStateCodec()
    auth_attempt_repository = FakeAuthAttemptRepository()
    attempt = auth_attempt_repository.add(
        AuthAttempt.create(
            return_to="/compare",
            code_verifier="pkce-verifier-1",
            ttl=timedelta(minutes=15),
            issued_at=fixed_now - timedelta(minutes=1),
        )
    )
    state = auth_state_codec.issue(attempt_id=attempt.id)
    user_repository = FakeUserRepository()
    existing_user = user_repository.add_user(
        UserAccount.create(email="person@example.com", created_at=fixed_now - timedelta(days=3))
    )
    session_repository = FakeSessionRepository()
    use_case = CompleteAuthCallbackUseCase(
        identity_provider=provider,
        auth_flow_state_codec=auth_state_codec,
        auth_attempt_repository=auth_attempt_repository,
        user_repository=user_repository,
        session_repository=session_repository,
        session_ttl=timedelta(days=14),
        clock=lambda: fixed_now,
    )

    result = use_case.execute(
        callback_params={"state": state, "ticket": "valid-ticket"},
        callback_url="http://testserver/api/v1/auth/callback",
    )

    assert result.user.id == existing_user.id
    assert len(user_repository.users_by_id) == 1
    assert result.session_token in session_repository.sessions


def test_get_current_session_returns_anonymous_reasons_for_invalid_and_expired_tokens() -> None:
    fixed_now = datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc)
    user_repository = FakeUserRepository()
    session_repository = FakeSessionRepository()
    use_case = GetCurrentSessionUseCase(
        user_repository=user_repository,
        session_repository=session_repository,
        clock=lambda: fixed_now,
    )

    invalid = use_case.execute(session_token="missing-token")
    assert invalid.state == "anonymous"
    assert invalid.anonymous_reason == "invalid"
    assert invalid.user is None

    user = user_repository.add_user(
        UserAccount.create(email="person@example.com", created_at=fixed_now - timedelta(days=1))
    )
    expired_session = session_repository.add(
        AppSession(
            token="expired-token",
            user_id=user.id,
            issued_at=fixed_now - timedelta(days=2),
            last_seen_at=fixed_now - timedelta(days=2),
            expires_at=fixed_now - timedelta(seconds=1),
            revoked_at=None,
            revoke_reason=None,
        )
    )
    assert expired_session.token == "expired-token"

    expired = use_case.execute(session_token="expired-token")
    assert expired.state == "anonymous"
    assert expired.anonymous_reason == "expired"
    assert session_repository.sessions["expired-token"].revoke_reason == "expired"


def test_sign_out_revokes_existing_session() -> None:
    fixed_now = datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc)
    user_repository = FakeUserRepository()
    session_repository = FakeSessionRepository()
    user = user_repository.add_user(
        UserAccount.create(email="person@example.com", created_at=fixed_now - timedelta(days=1))
    )
    session_repository.add(
        AppSession(
            token="live-token",
            user_id=user.id,
            issued_at=fixed_now - timedelta(hours=1),
            last_seen_at=fixed_now - timedelta(minutes=5),
            expires_at=fixed_now + timedelta(days=7),
            revoked_at=None,
            revoke_reason=None,
        )
    )

    use_case = SignOutUseCase(
        session_repository=session_repository,
        clock=lambda: fixed_now,
    )

    result = use_case.execute(session_token="live-token")

    assert result.state == "anonymous"
    assert result.anonymous_reason == "signed_out"
    assert session_repository.sessions["live-token"].revoked_at == fixed_now
    assert session_repository.sessions["live-token"].revoke_reason == "signed_out"


def test_complete_auth_callback_rejects_invalid_state() -> None:
    provider = FakeIdentityProvider()
    use_case = CompleteAuthCallbackUseCase(
        identity_provider=provider,
        auth_flow_state_codec=FakeAuthFlowStateCodec(),
        auth_attempt_repository=FakeAuthAttemptRepository(),
        user_repository=FakeUserRepository(),
        session_repository=FakeSessionRepository(),
        session_ttl=timedelta(days=14),
    )

    with pytest.raises(InvalidAuthCallbackError, match="invalid auth state"):
        use_case.execute(
            callback_params={"state": "unknown-state", "ticket": "valid-ticket"},
            callback_url="http://testserver/api/v1/auth/callback",
        )


def test_complete_auth_callback_rejects_unverified_email_before_linking_or_session_creation() -> (
    None
):
    fixed_now = datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc)
    provider = FakeIdentityProvider(
        resolved_user=IdentityProviderUserDto(
            provider_name="development",
            provider_subject="person@example.com",
            email="person@example.com",
            email_verified=False,
        )
    )
    auth_state_codec = FakeAuthFlowStateCodec()
    auth_attempt_repository = FakeAuthAttemptRepository()
    attempt = auth_attempt_repository.add(
        AuthAttempt.create(
            return_to="/compare",
            code_verifier="pkce-verifier-1",
            ttl=timedelta(minutes=15),
            issued_at=fixed_now - timedelta(minutes=1),
        )
    )
    state = auth_state_codec.issue(attempt_id=attempt.id)
    user_repository = FakeUserRepository()
    existing_user = user_repository.add_user(
        UserAccount.create(
            email="person@example.com",
            created_at=datetime(2026, 3, 6, 10, 0, tzinfo=timezone.utc),
        )
    )
    session_repository = FakeSessionRepository()
    use_case = CompleteAuthCallbackUseCase(
        identity_provider=provider,
        auth_flow_state_codec=auth_state_codec,
        auth_attempt_repository=auth_attempt_repository,
        user_repository=user_repository,
        session_repository=session_repository,
        session_ttl=timedelta(days=14),
        clock=lambda: fixed_now,
    )

    with pytest.raises(InvalidAuthCallbackError, match="verified"):
        use_case.execute(
            callback_params={"state": state, "ticket": "valid-ticket"},
            callback_url="http://testserver/api/v1/auth/callback",
        )

    assert user_repository.get_by_email(email="person@example.com") == existing_user
    assert user_repository.identities == {}
    assert session_repository.sessions == {}


def test_complete_auth_callback_rejects_reused_auth_attempt() -> None:
    fixed_now = datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc)
    provider = FakeIdentityProvider()
    auth_state_codec = FakeAuthFlowStateCodec()
    auth_attempt_repository = FakeAuthAttemptRepository()
    attempt = auth_attempt_repository.add(
        AuthAttempt.create(
            return_to="/compare",
            code_verifier="pkce-verifier-1",
            ttl=timedelta(minutes=15),
            issued_at=fixed_now - timedelta(minutes=1),
        )
    )
    state = auth_state_codec.issue(attempt_id=attempt.id)

    use_case = CompleteAuthCallbackUseCase(
        identity_provider=provider,
        auth_flow_state_codec=auth_state_codec,
        auth_attempt_repository=auth_attempt_repository,
        user_repository=FakeUserRepository(),
        session_repository=FakeSessionRepository(),
        session_ttl=timedelta(days=14),
        clock=lambda: fixed_now,
    )

    use_case.execute(
        callback_params={"state": state, "ticket": "valid-ticket"},
        callback_url="http://testserver/api/v1/auth/callback",
    )

    with pytest.raises(InvalidAuthCallbackError, match="invalid auth state"):
        use_case.execute(
            callback_params={"state": state, "ticket": "valid-ticket"},
            callback_url="http://testserver/api/v1/auth/callback",
        )


def test_complete_auth_callback_rejects_expired_auth_attempt() -> None:
    fixed_now = datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc)
    provider = FakeIdentityProvider()
    auth_state_codec = FakeAuthFlowStateCodec()
    auth_attempt_repository = FakeAuthAttemptRepository()
    attempt = auth_attempt_repository.add(
        AuthAttempt(
            id="attempt-1",
            return_to="/compare",
            code_verifier="pkce-verifier-1",
            issued_at=fixed_now - timedelta(minutes=16),
            expires_at=fixed_now - timedelta(minutes=1),
            consumed_at=None,
        )
    )
    state = auth_state_codec.issue(attempt_id=attempt.id)

    use_case = CompleteAuthCallbackUseCase(
        identity_provider=provider,
        auth_flow_state_codec=auth_state_codec,
        auth_attempt_repository=auth_attempt_repository,
        user_repository=FakeUserRepository(),
        session_repository=FakeSessionRepository(),
        session_ttl=timedelta(days=14),
        clock=lambda: fixed_now,
    )

    with pytest.raises(InvalidAuthCallbackError, match="invalid auth state"):
        use_case.execute(
            callback_params={"state": state, "ticket": "valid-ticket"},
            callback_url="http://testserver/api/v1/auth/callback",
        )
