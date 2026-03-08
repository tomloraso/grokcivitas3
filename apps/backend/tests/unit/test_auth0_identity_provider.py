from __future__ import annotations

from collections.abc import Iterator
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from civitas.application.identity.errors import (
    IdentityProviderUnavailableError,
    InvalidAuthCallbackError,
)
from civitas.infrastructure.auth.auth0_identity_provider import Auth0IdentityProvider


def test_auth0_start_sign_in_builds_authorize_url() -> None:
    provider = Auth0IdentityProvider(
        domain="tenant.example.eu.auth0.com",
        client_id="auth0-client-id",
        client_secret="auth0-client-secret",
        audience="https://api.example.test",
        connection="email",
        http_client=httpx.Client(transport=httpx.MockTransport(_unexpected_request)),
    )

    redirect_url = provider.start_sign_in(
        email="person@example.com",
        state="state-1",
        callback_url="https://api.example.test/api/v1/auth/callback",
        code_challenge="pkce-challenge-1",
        code_challenge_method="S256",
    )

    parsed = urlparse(redirect_url)
    params = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "tenant.example.eu.auth0.com"
    assert parsed.path == "/authorize"
    assert params == {
        "audience": ["https://api.example.test"],
        "client_id": ["auth0-client-id"],
        "code_challenge": ["pkce-challenge-1"],
        "code_challenge_method": ["S256"],
        "connection": ["email"],
        "login_hint": ["person@example.com"],
        "redirect_uri": ["https://api.example.test/api/v1/auth/callback"],
        "response_type": ["code"],
        "scope": ["openid profile email"],
        "state": ["state-1"],
    }


def test_auth0_complete_sign_in_exchanges_code_and_maps_userinfo() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/oauth/token":
            return httpx.Response(
                200,
                json={
                    "access_token": "access-token-1",
                    "token_type": "Bearer",
                },
            )
        if request.url.path == "/userinfo":
            return httpx.Response(
                200,
                json={
                    "sub": "auth0|user-123",
                    "email": "person@example.com",
                    "email_verified": True,
                },
            )
        raise AssertionError(f"Unexpected request path: {request.url.path}")

    provider = Auth0IdentityProvider(
        domain="tenant.example.eu.auth0.com",
        client_id="auth0-client-id",
        client_secret="auth0-client-secret",
        connection="email",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = provider.complete_sign_in(
        callback_params={"state": "state-1", "code": "authorization-code"},
        callback_url="https://api.example.test/api/v1/auth/callback",
        code_verifier="pkce-verifier-1",
    )

    assert result.provider_name == "auth0"
    assert result.provider_subject == "auth0|user-123"
    assert result.email == "person@example.com"
    assert result.email_verified is True
    assert [request.url.path for request in requests] == ["/oauth/token", "/userinfo"]

    token_request = requests[0]
    token_body = dict(_parse_form_body(token_request))
    assert token_request.method == "POST"
    assert token_body == {
        "client_id": "auth0-client-id",
        "client_secret": "auth0-client-secret",
        "code": "authorization-code",
        "code_verifier": "pkce-verifier-1",
        "grant_type": "authorization_code",
        "redirect_uri": "https://api.example.test/api/v1/auth/callback",
    }

    userinfo_request = requests[1]
    assert userinfo_request.method == "GET"
    assert userinfo_request.headers["Authorization"] == "Bearer access-token-1"


def test_auth0_complete_sign_in_rejects_provider_error_callback_without_network() -> None:
    provider = Auth0IdentityProvider(
        domain="tenant.example.eu.auth0.com",
        client_id="auth0-client-id",
        client_secret="auth0-client-secret",
        connection="email",
        http_client=httpx.Client(transport=httpx.MockTransport(_unexpected_request)),
    )

    with pytest.raises(InvalidAuthCallbackError, match="provider callback could not be verified"):
        provider.complete_sign_in(
            callback_params={
                "state": "state-1",
                "error": "access_denied",
                "error_description": "User canceled the flow.",
            },
            callback_url="https://api.example.test/api/v1/auth/callback",
            code_verifier="pkce-verifier-1",
        )


def test_auth0_complete_sign_in_raises_provider_unavailable_for_network_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    provider = Auth0IdentityProvider(
        domain="tenant.example.eu.auth0.com",
        client_id="auth0-client-id",
        client_secret="auth0-client-secret",
        connection="email",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(IdentityProviderUnavailableError, match="Auth0 is unavailable"):
        provider.complete_sign_in(
            callback_params={"state": "state-1", "code": "authorization-code"},
            callback_url="https://api.example.test/api/v1/auth/callback",
            code_verifier="pkce-verifier-1",
        )


def test_auth0_complete_sign_in_rejects_missing_email_claim() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/token":
            return httpx.Response(
                200,
                json={
                    "access_token": "access-token-1",
                    "token_type": "Bearer",
                },
            )
        if request.url.path == "/userinfo":
            return httpx.Response(
                200,
                json={
                    "sub": "auth0|user-123",
                    "email_verified": True,
                },
            )
        raise AssertionError(f"Unexpected request path: {request.url.path}")

    provider = Auth0IdentityProvider(
        domain="tenant.example.eu.auth0.com",
        client_id="auth0-client-id",
        client_secret="auth0-client-secret",
        connection="email",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(InvalidAuthCallbackError, match="email address"):
        provider.complete_sign_in(
            callback_params={"state": "state-1", "code": "authorization-code"},
            callback_url="https://api.example.test/api/v1/auth/callback",
            code_verifier="pkce-verifier-1",
        )


def test_auth0_complete_sign_in_requires_code_verifier() -> None:
    provider = Auth0IdentityProvider(
        domain="tenant.example.eu.auth0.com",
        client_id="auth0-client-id",
        client_secret="auth0-client-secret",
        connection="email",
        http_client=httpx.Client(transport=httpx.MockTransport(_unexpected_request)),
    )

    with pytest.raises(InvalidAuthCallbackError, match="provider callback could not be verified"):
        provider.complete_sign_in(
            callback_params={"state": "state-1", "code": "authorization-code"},
            callback_url="https://api.example.test/api/v1/auth/callback",
            code_verifier=None,
        )


def _parse_form_body(request: httpx.Request) -> Iterator[tuple[str, str]]:
    return (
        (key, values[0])
        for key, values in parse_qs(request.content.decode("utf-8"), keep_blank_values=True).items()
    )


def _unexpected_request(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"Unexpected request: {request.method} {request.url}")
