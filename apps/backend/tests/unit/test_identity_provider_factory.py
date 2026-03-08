from __future__ import annotations

import pytest

from civitas.infrastructure.auth.auth0_identity_provider import Auth0IdentityProvider
from civitas.infrastructure.auth.development_identity_provider import DevelopmentIdentityProvider
from civitas.infrastructure.auth.provider_factory import build_identity_provider
from civitas.infrastructure.config.settings import AppSettings


def test_build_identity_provider_returns_development_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_AUTH_PROVIDER", "development")

    settings = AppSettings(_env_file=None)

    assert isinstance(build_identity_provider(settings), DevelopmentIdentityProvider)


def test_build_identity_provider_returns_auth0_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_AUTH_PROVIDER", "auth0")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_DOMAIN", "tenant.example.eu.auth0.com")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_CLIENT_ID", "auth0-client-id")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_CLIENT_SECRET", "auth0-client-secret")

    settings = AppSettings(_env_file=None)

    assert isinstance(build_identity_provider(settings), Auth0IdentityProvider)
