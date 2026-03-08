from __future__ import annotations

from unittest.mock import sentinel

from tests.fixtures import integration_database
from tests.fixtures.integration_database import (
    build_integration_engine,
    integration_database_available,
    integration_database_url,
)


def test_integration_database_url_prefers_explicit_test_database(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "CIVITAS_TEST_DATABASE_URL",
        "postgresql+psycopg://app:app@localhost:5432/app_test",
    )
    monkeypatch.setenv(
        "CIVITAS_DATABASE_URL",
        "postgresql+psycopg://app:app@localhost:5432/app",
    )

    assert integration_database_url() == "postgresql+psycopg://app:app@localhost:5432/app_test"


def test_integration_database_url_accepts_test_scoped_database_name(
    monkeypatch,
) -> None:
    monkeypatch.delenv("CIVITAS_TEST_DATABASE_URL", raising=False)
    monkeypatch.setenv(
        "CIVITAS_DATABASE_URL",
        "postgresql+psycopg://app:app@localhost:5432/app_test",
    )

    assert integration_database_url() == "postgresql+psycopg://app:app@localhost:5432/app_test"


def test_integration_database_url_rejects_default_app_database(
    monkeypatch,
) -> None:
    monkeypatch.delenv("CIVITAS_TEST_DATABASE_URL", raising=False)
    monkeypatch.setenv(
        "CIVITAS_DATABASE_URL",
        "postgresql+psycopg://app:app@localhost:5432/app",
    )

    assert integration_database_url() is None


def test_build_integration_engine_sets_postgres_search_path_when_requested(
    monkeypatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    def fake_create_engine(*args, **kwargs):  # type: ignore[no-untyped-def]
        captured_kwargs["args"] = args
        captured_kwargs["kwargs"] = kwargs
        return sentinel.engine

    monkeypatch.setattr(integration_database, "create_engine", fake_create_engine)

    engine = build_integration_engine(
        "postgresql+psycopg://app:app@localhost:5432/app_test",
        schema_name="integration_schema",
    )

    assert engine is sentinel.engine
    assert captured_kwargs["args"] == ("postgresql+psycopg://app:app@localhost:5432/app_test",)
    assert captured_kwargs["kwargs"] == {
        "future": True,
        "connect_args": {
            "connect_timeout": 2,
            "options": "-csearch_path=integration_schema,public",
        },
    }


def test_integration_database_available_returns_false_without_database_url() -> None:
    assert integration_database_available(None) is False
