from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone

from civitas.application.identity.dto import (
    CompleteAuthCallbackResultDto,
    CurrentSessionDto,
    SessionUserDto,
    StartSignInResultDto,
)
from civitas.application.identity.errors import InvalidAuthCallbackError, InvalidSignInEmailError
from civitas.application.identity.ports.auth_attempt_repository import AuthAttemptRepository
from civitas.application.identity.ports.auth_flow_state_codec import AuthFlowStateCodec
from civitas.application.identity.ports.identity_provider import IdentityProvider
from civitas.application.identity.ports.session_repository import SessionRepository
from civitas.application.identity.ports.user_repository import UserRepository
from civitas.application.shared.utils.safe_redirects import normalize_return_to
from civitas.domain.identity.models import AppSession, AuthAttempt, AuthIdentity, UserAccount
from civitas.domain.identity.services import (
    derive_pkce_code_challenge,
    generate_pkce_code_verifier,
    normalize_email,
)

Clock = Callable[[], datetime]
PkceCodeVerifierFactory = Callable[[], str]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StartSignInUseCase:
    def __init__(
        self,
        *,
        identity_provider: IdentityProvider,
        auth_flow_state_codec: AuthFlowStateCodec,
        auth_attempt_repository: AuthAttemptRepository,
        auth_attempt_ttl: timedelta,
        pkce_code_verifier_factory: PkceCodeVerifierFactory = generate_pkce_code_verifier,
    ) -> None:
        self._identity_provider = identity_provider
        self._auth_flow_state_codec = auth_flow_state_codec
        self._auth_attempt_repository = auth_attempt_repository
        self._auth_attempt_ttl = auth_attempt_ttl
        self._pkce_code_verifier_factory = pkce_code_verifier_factory

    def execute(
        self,
        *,
        email: str,
        return_to: str | None,
        callback_url: str,
    ) -> StartSignInResultDto:
        try:
            normalized_email = normalize_email(email)
        except ValueError as exc:
            raise InvalidSignInEmailError(str(exc)) from exc

        normalized_return_to = normalize_return_to(return_to)
        code_verifier = self._pkce_code_verifier_factory()
        auth_attempt = self._auth_attempt_repository.add(
            AuthAttempt.create(
                return_to=normalized_return_to,
                code_verifier=code_verifier,
                ttl=self._auth_attempt_ttl,
            )
        )
        state = self._auth_flow_state_codec.issue(attempt_id=auth_attempt.id)
        redirect_url = self._identity_provider.start_sign_in(
            email=normalized_email,
            state=state,
            callback_url=callback_url,
            code_challenge=derive_pkce_code_challenge(code_verifier),
            code_challenge_method="S256",
        )
        return StartSignInResultDto(redirect_url=redirect_url)


class CompleteAuthCallbackUseCase:
    def __init__(
        self,
        *,
        identity_provider: IdentityProvider,
        auth_flow_state_codec: AuthFlowStateCodec,
        auth_attempt_repository: AuthAttemptRepository,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        session_ttl: timedelta,
        clock: Clock = _utc_now,
    ) -> None:
        self._identity_provider = identity_provider
        self._auth_flow_state_codec = auth_flow_state_codec
        self._auth_attempt_repository = auth_attempt_repository
        self._user_repository = user_repository
        self._session_repository = session_repository
        self._session_ttl = session_ttl
        self._clock = clock

    def execute(
        self,
        *,
        callback_params: Mapping[str, str],
        callback_url: str,
    ) -> CompleteAuthCallbackResultDto:
        state = callback_params.get("state", "").strip()
        if not state:
            raise InvalidAuthCallbackError("invalid auth state")

        auth_state = self._auth_flow_state_codec.read(state=state)
        now = self._clock()
        auth_attempt = self._auth_attempt_repository.consume(
            attempt_id=auth_state.attempt_id,
            now=now,
        )
        if auth_attempt is None:
            raise InvalidAuthCallbackError("invalid auth state")

        provider_user = self._identity_provider.complete_sign_in(
            callback_params=callback_params,
            callback_url=callback_url,
            code_verifier=auth_attempt.code_verifier,
        )
        if not provider_user.email_verified:
            raise InvalidAuthCallbackError("email address must be verified")

        user = self._user_repository.get_by_auth_identity(
            provider_name=provider_user.provider_name,
            provider_subject=provider_user.provider_subject,
        )
        if user is None:
            user = self._user_repository.get_by_email(email=provider_user.email)
        if user is None:
            user = self._user_repository.add_user(
                UserAccount.create(email=provider_user.email, created_at=now)
            )

        self._user_repository.upsert_auth_identity(
            AuthIdentity.create(
                user_id=user.id,
                provider_name=provider_user.provider_name,
                provider_subject=provider_user.provider_subject,
                email=provider_user.email,
                email_verified=provider_user.email_verified,
                created_at=now,
            )
        )
        self._user_repository.update_user_last_sign_in(user_id=user.id, signed_in_at=now)

        session = self._session_repository.add(
            AppSession.create(
                user_id=user.id,
                ttl=self._session_ttl,
                issued_at=now,
            )
        )
        return CompleteAuthCallbackResultDto(
            return_to=auth_attempt.return_to,
            session_token=session.token,
            expires_at=session.expires_at,
            user=SessionUserDto(id=user.id, email=user.email),
        )


class GetCurrentSessionUseCase:
    def __init__(
        self,
        *,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        clock: Clock = _utc_now,
    ) -> None:
        self._user_repository = user_repository
        self._session_repository = session_repository
        self._clock = clock

    def execute(self, *, session_token: str | None) -> CurrentSessionDto:
        if session_token is None or not session_token.strip():
            return CurrentSessionDto.anonymous(reason="missing")

        normalized_token = session_token.strip()
        session = self._session_repository.get_by_token(token=normalized_token)
        if session is None:
            return CurrentSessionDto.anonymous(reason="invalid")

        now = self._clock()
        if session.revoked_at is not None:
            return CurrentSessionDto.anonymous(reason="revoked")
        if session.is_expired(at=now):
            self._session_repository.revoke(
                token=normalized_token,
                revoked_at=now,
                reason="expired",
            )
            return CurrentSessionDto.anonymous(reason="expired")

        user = self._user_repository.get_by_id(user_id=session.user_id)
        if user is None:
            self._session_repository.revoke(
                token=normalized_token,
                revoked_at=now,
                reason="invalid",
            )
            return CurrentSessionDto.anonymous(reason="invalid")

        self._session_repository.touch(token=normalized_token, last_seen_at=now)
        return CurrentSessionDto.authenticated(
            user=SessionUserDto(id=user.id, email=user.email),
            expires_at=session.expires_at,
        )


class SignOutUseCase:
    def __init__(
        self,
        *,
        session_repository: SessionRepository,
        clock: Clock = _utc_now,
    ) -> None:
        self._session_repository = session_repository
        self._clock = clock

    def execute(self, *, session_token: str | None) -> CurrentSessionDto:
        if session_token is not None and session_token.strip():
            self._session_repository.revoke(
                token=session_token.strip(),
                revoked_at=self._clock(),
                reason="signed_out",
            )
        return CurrentSessionDto.anonymous(reason="signed_out")
