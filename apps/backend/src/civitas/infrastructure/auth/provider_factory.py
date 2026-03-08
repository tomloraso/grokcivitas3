from __future__ import annotations

from datetime import timedelta

from civitas.application.identity.ports.identity_provider import IdentityProvider
from civitas.infrastructure.auth.auth0_identity_provider import Auth0IdentityProvider
from civitas.infrastructure.auth.development_identity_provider import DevelopmentIdentityProvider
from civitas.infrastructure.config.settings import AppSettings


def build_identity_provider(settings: AppSettings) -> IdentityProvider:
    if settings.auth.provider == "development":
        return DevelopmentIdentityProvider(
            shared_secret=settings.auth.shared_secret,
            ttl=timedelta(minutes=settings.auth.state_ttl_minutes),
        )

    auth0_settings = settings.auth.auth0
    if settings.auth.provider == "auth0" and auth0_settings is not None:
        return Auth0IdentityProvider(
            domain=auth0_settings.domain,
            client_id=auth0_settings.client_id,
            client_secret=auth0_settings.client_secret,
            audience=auth0_settings.audience,
            connection=auth0_settings.connection,
            timeout_seconds=settings.http_clients.timeout_seconds,
        )

    raise ValueError(f"Unsupported auth provider: {settings.auth.provider}")
