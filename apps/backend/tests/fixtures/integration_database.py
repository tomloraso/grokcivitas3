from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url

from civitas.infrastructure.config.settings import AppSettings

INTEGRATION_DATABASE_SKIP_REASON = (
    "Postgres integration tests require CIVITAS_TEST_DATABASE_URL or a test-scoped "
    "CIVITAS_DATABASE_URL; refusing to use the app database."
)


def integration_database_url() -> str | None:
    settings = AppSettings()

    explicit_database_url = (settings.test_database_url or "").strip()
    if explicit_database_url:
        return explicit_database_url

    configured_database_url = settings.database.url.strip()
    if _is_test_scoped_database_url(configured_database_url):
        return configured_database_url
    return None


def build_integration_engine(database_url: str, *, schema_name: str | None = None) -> Engine:
    connect_args: dict[str, object] = {}
    if database_url.startswith("postgresql"):
        connect_args["connect_timeout"] = 2
        if schema_name is not None:
            connect_args["options"] = f"-csearch_path={schema_name},public"
    return create_engine(
        database_url,
        future=True,
        connect_args=connect_args,
    )


def integration_database_available(database_url: str | None) -> bool:
    if database_url is None:
        return False

    engine = build_integration_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


def _is_test_scoped_database_url(database_url: str) -> bool:
    if not database_url:
        return False

    try:
        parsed_url = make_url(database_url)
    except Exception:
        return False

    backend_name = parsed_url.get_backend_name().lower()
    database_name = (parsed_url.database or "").strip()
    if backend_name == "sqlite":
        if database_name in {"", ":memory:"}:
            return True
        return "test" in Path(database_name).stem.lower()

    normalized_database_name = database_name.lower()
    return (
        normalized_database_name.endswith("_test")
        or normalized_database_name.endswith("-test")
        or normalized_database_name.startswith("test_")
        or normalized_database_name.startswith("test-")
    )
