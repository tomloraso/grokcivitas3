from __future__ import annotations

import pytest

from civitas.infrastructure.config.settings import (
    DEFAULT_AUTH_ALLOWED_ORIGINS,
    DEFAULT_AUTH_AUTH0_CONNECTION,
    DEFAULT_AUTH_CALLBACK_ERROR_PATH,
    DEFAULT_AUTH_PROVIDER,
    DEFAULT_AUTH_SESSION_COOKIE_NAME,
    DEFAULT_AUTH_SESSION_COOKIE_SAMESITE,
    DEFAULT_AUTH_SESSION_COOKIE_SECURE,
    DEFAULT_AUTH_SESSION_TTL_HOURS,
    DEFAULT_AUTH_STATE_TTL_MINUTES,
    DEFAULT_RUNTIME_ENVIRONMENT,
    AppSettings,
)


def test_auth_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "CIVITAS_AUTH_PROVIDER",
        "CIVITAS_AUTH_SESSION_COOKIE_NAME",
        "CIVITAS_AUTH_SESSION_COOKIE_SECURE",
        "CIVITAS_AUTH_SESSION_COOKIE_SAMESITE",
        "CIVITAS_AUTH_SESSION_TTL_HOURS",
        "CIVITAS_AUTH_STATE_TTL_MINUTES",
        "CIVITAS_AUTH_CALLBACK_ERROR_PATH",
        "CIVITAS_AUTH_ALLOWED_ORIGINS",
        "CIVITAS_AUTH_SHARED_SECRET",
        "CIVITAS_AUTH_AUTH0_DOMAIN",
        "CIVITAS_AUTH_AUTH0_CLIENT_ID",
        "CIVITAS_AUTH_AUTH0_CLIENT_SECRET",
        "CIVITAS_AUTH_AUTH0_AUDIENCE",
        "CIVITAS_AUTH_AUTH0_CONNECTION",
        "CIVITAS_RUNTIME_ENVIRONMENT",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = AppSettings(_env_file=None)

    assert settings.auth.provider == DEFAULT_AUTH_PROVIDER
    assert settings.auth.session_cookie_name == DEFAULT_AUTH_SESSION_COOKIE_NAME
    assert settings.auth.session_cookie_secure is DEFAULT_AUTH_SESSION_COOKIE_SECURE
    assert settings.auth.session_cookie_samesite == DEFAULT_AUTH_SESSION_COOKIE_SAMESITE
    assert settings.auth.session_ttl_hours == DEFAULT_AUTH_SESSION_TTL_HOURS
    assert settings.auth.state_ttl_minutes == DEFAULT_AUTH_STATE_TTL_MINUTES
    assert settings.auth.callback_error_path == DEFAULT_AUTH_CALLBACK_ERROR_PATH
    assert settings.auth.allowed_origins == tuple(DEFAULT_AUTH_ALLOWED_ORIGINS.split(","))
    assert settings.auth.shared_secret
    assert settings.auth.auth0 is None
    assert settings.runtime_environment == DEFAULT_RUNTIME_ENVIRONMENT


def test_auth_settings_read_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIVITAS_AUTH_PROVIDER", "development")
    monkeypatch.setenv("CIVITAS_AUTH_SESSION_COOKIE_NAME", " civitas_test_session ")
    monkeypatch.setenv("CIVITAS_AUTH_SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("CIVITAS_AUTH_SESSION_COOKIE_SAMESITE", " strict ")
    monkeypatch.setenv("CIVITAS_AUTH_SESSION_TTL_HOURS", "336")
    monkeypatch.setenv("CIVITAS_AUTH_STATE_TTL_MINUTES", "30")
    monkeypatch.setenv("CIVITAS_AUTH_CALLBACK_ERROR_PATH", " /sign-in ")
    monkeypatch.setenv(
        "CIVITAS_AUTH_ALLOWED_ORIGINS",
        " http://localhost:5173, http://127.0.0.1:8000 ",
    )
    monkeypatch.setenv("CIVITAS_AUTH_SHARED_SECRET", " local-dev-secret ")
    monkeypatch.setenv("CIVITAS_RUNTIME_ENVIRONMENT", " test ")

    settings = AppSettings(_env_file=None)

    assert settings.auth.provider == "development"
    assert settings.auth.session_cookie_name == "civitas_test_session"
    assert settings.auth.session_cookie_secure is True
    assert settings.auth.session_cookie_samesite == "strict"
    assert settings.auth.session_ttl_hours == 336
    assert settings.auth.state_ttl_minutes == 30
    assert settings.auth.callback_error_path == "/sign-in"
    assert settings.auth.allowed_origins == (
        "http://localhost:5173",
        "http://127.0.0.1:8000",
    )
    assert settings.auth.shared_secret == "local-dev-secret"
    assert settings.runtime_environment == "test"


def test_auth_settings_reject_invalid_samesite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIVITAS_AUTH_SESSION_COOKIE_SAMESITE", "invalid")

    with pytest.raises(ValueError, match="CIVITAS_AUTH_SESSION_COOKIE_SAMESITE"):
        AppSettings(_env_file=None)


def test_auth_settings_require_secure_cookie_when_samesite_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_AUTH_SESSION_COOKIE_SAMESITE", "none")
    monkeypatch.setenv("CIVITAS_AUTH_SESSION_COOKIE_SECURE", "false")

    with pytest.raises(ValueError, match="CIVITAS_AUTH_SESSION_COOKIE_SECURE"):
        AppSettings(_env_file=None)


def test_auth_settings_reject_development_provider_outside_local_or_test(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_RUNTIME_ENVIRONMENT", "staging")
    monkeypatch.setenv("CIVITAS_AUTH_PROVIDER", "development")
    monkeypatch.setenv("CIVITAS_AUTH_SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("CIVITAS_AUTH_ALLOWED_ORIGINS", "https://app.example.test")
    monkeypatch.setenv("CIVITAS_AUTH_SHARED_SECRET", "not-the-default-secret")

    with pytest.raises(ValueError, match="CIVITAS_AUTH_PROVIDER=development"):
        AppSettings(_env_file=None)


def test_auth_settings_reject_development_provider_with_non_local_allowed_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_AUTH_PROVIDER", "development")
    monkeypatch.setenv("CIVITAS_AUTH_ALLOWED_ORIGINS", "https://app.example.test")

    with pytest.raises(
        ValueError,
        match="requires localhost, loopback, or testserver auth allowed origins",
    ):
        AppSettings(_env_file=None)


def test_auth_settings_require_allowed_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_AUTH_ALLOWED_ORIGINS", "")

    with pytest.raises(ValueError, match="CIVITAS_AUTH_ALLOWED_ORIGINS"):
        AppSettings(_env_file=None)


def test_auth_settings_require_auth0_configuration_when_provider_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_AUTH_PROVIDER", "auth0")

    with pytest.raises(
        ValueError,
        match=(
            "CIVITAS_AUTH_AUTH0_DOMAIN, CIVITAS_AUTH_AUTH0_CLIENT_ID, and "
            "CIVITAS_AUTH_AUTH0_CLIENT_SECRET must be set"
        ),
    ):
        AppSettings(_env_file=None)


def test_auth_settings_read_auth0_environment_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_AUTH_PROVIDER", "auth0")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_DOMAIN", " tenant.example.eu.auth0.com ")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_CLIENT_ID", " auth0-client-id ")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_CLIENT_SECRET", " auth0-client-secret ")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_AUDIENCE", " https://api.example.test ")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_CONNECTION", " email ")

    settings = AppSettings(_env_file=None)

    assert settings.auth.provider == "auth0"
    assert settings.auth.auth0 is not None
    assert settings.auth.auth0.domain == "tenant.example.eu.auth0.com"
    assert settings.auth.auth0.client_id == "auth0-client-id"
    assert settings.auth.auth0.client_secret == "auth0-client-secret"
    assert settings.auth.auth0.audience == "https://api.example.test"
    assert settings.auth.auth0.connection == DEFAULT_AUTH_AUTH0_CONNECTION


def test_auth_settings_reject_invalid_auth0_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVITAS_AUTH_PROVIDER", "auth0")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_DOMAIN", "https://tenant.example.eu.auth0.com/path")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_CLIENT_ID", "auth0-client-id")
    monkeypatch.setenv("CIVITAS_AUTH_AUTH0_CLIENT_SECRET", "auth0-client-secret")

    with pytest.raises(ValueError, match="CIVITAS_AUTH_AUTH0_DOMAIN"):
        AppSettings(_env_file=None)
