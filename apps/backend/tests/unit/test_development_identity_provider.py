from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest

from civitas.application.identity.errors import InvalidAuthCallbackError
from civitas.infrastructure.auth.development_identity_provider import (
    DevelopmentIdentityProvider,
)


def test_development_provider_round_trips_signed_ticket() -> None:
    fixed_now = datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc)
    provider = DevelopmentIdentityProvider(
        shared_secret="local-secret",
        ttl=timedelta(minutes=15),
        clock=lambda: fixed_now,
    )

    redirect_url = provider.start_sign_in(
        email=" Person@example.com ",
        state="state-1",
        callback_url="http://testserver/api/v1/auth/callback",
        code_challenge="ignored-pkce-challenge",
        code_challenge_method="S256",
    )

    parsed = urlparse(redirect_url)
    params = parse_qs(parsed.query)
    result = provider.complete_sign_in(
        callback_params={
            "state": params["state"][0],
            "ticket": params["ticket"][0],
        },
        callback_url="http://testserver/api/v1/auth/callback",
        code_verifier="ignored-code-verifier",
    )

    assert parsed.path == "/api/v1/auth/callback"
    assert params["state"] == ["state-1"]
    assert result.provider_name == "development"
    assert result.provider_subject == "person@example.com"
    assert result.email == "person@example.com"
    assert result.email_verified is True


def test_development_provider_rejects_missing_ticket() -> None:
    provider = DevelopmentIdentityProvider(
        shared_secret="local-secret",
        ttl=timedelta(minutes=15),
    )

    with pytest.raises(
        InvalidAuthCallbackError,
        match="provider callback could not be verified",
    ):
        provider.complete_sign_in(
            callback_params={"state": "state-1"},
            callback_url="http://testserver/api/v1/auth/callback",
        )


def test_development_provider_rejects_expired_ticket() -> None:
    issued_at = datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc)
    issuing_provider = DevelopmentIdentityProvider(
        shared_secret="local-secret",
        ttl=timedelta(minutes=15),
        clock=lambda: issued_at,
    )
    verifying_provider = DevelopmentIdentityProvider(
        shared_secret="local-secret",
        ttl=timedelta(minutes=15),
        clock=lambda: issued_at + timedelta(minutes=16),
    )

    redirect_url = issuing_provider.start_sign_in(
        email="person@example.com",
        state="state-1",
        callback_url="http://testserver/api/v1/auth/callback",
    )
    params = parse_qs(urlparse(redirect_url).query)

    with pytest.raises(
        InvalidAuthCallbackError,
        match="provider callback could not be verified",
    ):
        verifying_provider.complete_sign_in(
            callback_params={
                "state": params["state"][0],
                "ticket": params["ticket"][0],
            },
            callback_url="http://testserver/api/v1/auth/callback",
        )
