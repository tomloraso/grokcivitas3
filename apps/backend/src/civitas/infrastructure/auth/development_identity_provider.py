from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from civitas.application.identity.dto import IdentityProviderUserDto
from civitas.application.identity.errors import InvalidAuthCallbackError
from civitas.application.identity.ports.identity_provider import IdentityProvider
from civitas.domain.identity.services import normalize_email
from civitas.infrastructure.auth.signed_tokens import SignedTokenCodec

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DevelopmentIdentityProvider(IdentityProvider):
    def __init__(
        self,
        *,
        shared_secret: str,
        ttl: timedelta,
        clock: Clock = _utc_now,
    ) -> None:
        self._clock = clock
        self._ticket_codec = SignedTokenCodec(
            secret=shared_secret,
            ttl=ttl,
            purpose="development_identity_ticket",
        )

    def start_sign_in(
        self,
        *,
        email: str,
        state: str,
        callback_url: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> str:
        del code_challenge, code_challenge_method
        normalized_email = normalize_email(email)
        ticket = self._ticket_codec.issue(
            payload={"email": normalized_email},
            now=self._clock(),
        )
        separator = "&" if "?" in callback_url else "?"
        return (
            f"{callback_url}{separator}state={quote(state, safe='')}"
            f"&ticket={quote(ticket, safe='')}"
        )

    def complete_sign_in(
        self,
        *,
        callback_params: Mapping[str, str],
        callback_url: str,
        code_verifier: str | None = None,
    ) -> IdentityProviderUserDto:
        del callback_url, code_verifier
        ticket = callback_params.get("ticket", "").strip()
        if not ticket:
            raise InvalidAuthCallbackError("provider callback could not be verified")

        try:
            payload = self._ticket_codec.read(token=ticket, now=self._clock())
        except ValueError as exc:
            raise InvalidAuthCallbackError("provider callback could not be verified") from exc

        email = payload.get("email")
        if not isinstance(email, str):
            raise InvalidAuthCallbackError("provider callback could not be verified")

        normalized_email = normalize_email(email)
        return IdentityProviderUserDto(
            provider_name="development",
            provider_subject=normalized_email,
            email=normalized_email,
            email_verified=True,
        )
