from __future__ import annotations

import os
from pathlib import Path

import pytest

from civitas.infrastructure.config.settings import (
    DEFAULT_AUTH_ALLOWED_ORIGINS,
    get_settings,
)
from tests.fixtures.integration_database import (
    INTEGRATION_DATABASE_SKIP_REASON,
    integration_database_url,
)

_DISABLED_INTEGRATION_DATABASE_URL = (
    "postgresql+psycopg://disabled:disabled@127.0.0.1:1/civitas_integration_test"
)
INTEGRATION_DATABASE_URL = integration_database_url()
if INTEGRATION_DATABASE_URL is not None:
    os.environ["CIVITAS_DATABASE_URL"] = INTEGRATION_DATABASE_URL
else:
    os.environ["CIVITAS_DATABASE_URL"] = _DISABLED_INTEGRATION_DATABASE_URL
os.environ["CIVITAS_RUNTIME_ENVIRONMENT"] = "test"
os.environ["CIVITAS_AUTH_ALLOWED_ORIGINS"] = DEFAULT_AUTH_ALLOWED_ORIGINS
get_settings.cache_clear()


def pytest_report_header(config: pytest.Config) -> str | None:
    if INTEGRATION_DATABASE_URL is None:
        return f"backend integration tests disabled: {INTEGRATION_DATABASE_SKIP_REASON}"
    return None


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    if INTEGRATION_DATABASE_URL is not None:
        return

    skip_integration = pytest.mark.skip(reason=INTEGRATION_DATABASE_SKIP_REASON)
    for item in items:
        if _is_backend_integration_path(item.path):
            item.add_marker(skip_integration)


def _is_backend_integration_path(collection_path: Path) -> bool:
    normalized_path = collection_path.as_posix()
    return (
        normalized_path == "tests/integration"
        or normalized_path.startswith("tests/integration/")
        or "/tests/integration/" in normalized_path
        or normalized_path.endswith("/tests/integration")
    )
