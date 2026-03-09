from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from civitas.domain.access.models import EntitlementEvent, EntitlementGrant
from civitas.domain.identity.models import UserAccount
from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_entitlement_repository import (
    PostgresEntitlementRepository,
)
from civitas.infrastructure.persistence.postgres_product_repository import PostgresProductRepository
from civitas.infrastructure.persistence.postgres_user_repository import PostgresUserRepository

MIGRATION_PATHS = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20260307_26_phase_10_auth_session_foundation.py",
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20260308_27_phase_10_auth_pkce_hardening.py",
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20260309_29_phase_10_entitlements_domain_persistence.py",
)


def _database_url() -> str:
    return AppSettings().database.url


def _build_engine(database_url: str, *, schema_name: str | None = None) -> Engine:
    connect_args: dict[str, object] = {"connect_timeout": 2}
    if schema_name is not None:
        connect_args["options"] = f"-csearch_path={schema_name}"
    return create_engine(database_url, future=True, connect_args=connect_args)


def _database_available(database_url: str) -> bool:
    engine = _build_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


DATABASE_URL = _database_url()
DATABASE_AVAILABLE = DATABASE_URL.startswith("postgresql") and _database_available(DATABASE_URL)
pytestmark = pytest.mark.skipif(
    not DATABASE_AVAILABLE,
    reason="Postgres database unavailable for access repository integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    schema_name = f"test_access_{uuid4().hex}"
    admin_engine = _build_engine(DATABASE_URL)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))

    schema_engine = _build_engine(DATABASE_URL, schema_name=schema_name)
    _apply_migrations(schema_engine)

    try:
        yield schema_engine
    finally:
        schema_engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        admin_engine.dispose()


def _apply_migrations(engine: Engine) -> None:
    for migration_path in MIGRATION_PATHS:
        migration = _load_migration_module(migration_path)
        original_op = migration.op
        with engine.begin() as connection:
            migration_context = MigrationContext.configure(connection)
            migration.op = Operations(migration_context)
            try:
                migration.upgrade()
            finally:
                migration.op = original_op


def _load_migration_module(migration_path: Path):
    spec = importlib.util.spec_from_file_location(migration_path.stem, migration_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load migration module from {migration_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_access_migration_creates_expected_tables_indexes_and_seed_data(engine: Engine) -> None:
    inspector = inspect(engine)

    assert {
        "premium_products",
        "product_capabilities",
        "entitlements",
        "entitlement_events",
    }.issubset(set(inspector.get_table_names()))
    assert {index["name"] for index in inspector.get_indexes("product_capabilities")} == {
        "ix_product_capabilities_capability_key"
    }
    assert {index["name"] for index in inspector.get_indexes("entitlements")} == {
        "ix_entitlements_user_product_code",
        "ix_entitlements_user_status_ends_at",
    }
    assert {index["name"] for index in inspector.get_indexes("entitlement_events")} == {
        "ix_entitlement_events_entitlement_occurred_at",
        "ix_entitlement_events_provider_event_ref",
        "ix_entitlement_events_user_occurred_at",
    }

    product_repository = PostgresProductRepository(engine=engine)
    products = product_repository.list_available_products()

    assert len(products) == 1
    assert products[0].code == "premium_launch"
    assert products[0].display_name == "Premium"
    assert products[0].capability_keys == (
        "premium_ai_analyst",
        "premium_comparison",
        "premium_neighbourhood",
    )
    assert (
        product_repository.list_products_for_capability(capability_key="premium_ai_analyst")
        == products
    )


def test_entitlement_repository_persists_grants_and_current_capability_queries(
    engine: Engine,
) -> None:
    user_repository = PostgresUserRepository(engine=engine)
    entitlement_repository = PostgresEntitlementRepository(engine=engine)
    issued_at = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
    user = user_repository.add_user(
        UserAccount.create(email="premium@example.com", created_at=issued_at)
    )

    active = entitlement_repository.upsert_entitlement(
        EntitlementGrant(
            id=uuid4(),
            user_id=user.id,
            product_code="premium_launch",
            status="active",
            starts_at=issued_at - timedelta(days=1),
            ends_at=issued_at + timedelta(days=30),
            revoked_at=None,
            revoked_reason_code=None,
            created_at=issued_at,
            updated_at=issued_at,
        )
    )
    expired = entitlement_repository.upsert_entitlement(
        EntitlementGrant(
            id=uuid4(),
            user_id=user.id,
            product_code="premium_launch",
            status="active",
            starts_at=issued_at - timedelta(days=30),
            ends_at=issued_at - timedelta(minutes=1),
            revoked_at=None,
            revoked_reason_code=None,
            created_at=issued_at - timedelta(days=30),
            updated_at=issued_at - timedelta(days=1),
        )
    )
    revoked = entitlement_repository.upsert_entitlement(
        EntitlementGrant(
            id=uuid4(),
            user_id=user.id,
            product_code="premium_launch",
            status="revoked",
            starts_at=issued_at - timedelta(days=10),
            ends_at=issued_at + timedelta(days=20),
            revoked_at=issued_at - timedelta(hours=2),
            revoked_reason_code="refund",
            created_at=issued_at - timedelta(days=10),
            updated_at=issued_at - timedelta(hours=2),
        )
    )

    grants = entitlement_repository.list_user_entitlements(user_id=user.id)
    capability_keys = entitlement_repository.list_active_capability_keys(
        user_id=user.id,
        at=issued_at,
    )

    assert {grant.id for grant in grants} == {active.id, expired.id, revoked.id}
    assert capability_keys == (
        "premium_ai_analyst",
        "premium_comparison",
        "premium_neighbourhood",
    )
    assert (
        next(grant for grant in grants if grant.id == active.id).effective_status(at=issued_at)
        == "active"
    )
    assert (
        next(grant for grant in grants if grant.id == expired.id).effective_status(at=issued_at)
        == "expired"
    )
    assert (
        next(grant for grant in grants if grant.id == revoked.id).effective_status(at=issued_at)
        == "revoked"
    )


def test_entitlement_repository_records_append_only_events(engine: Engine) -> None:
    user_repository = PostgresUserRepository(engine=engine)
    entitlement_repository = PostgresEntitlementRepository(engine=engine)
    issued_at = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
    user = user_repository.add_user(
        UserAccount.create(email="events@example.com", created_at=issued_at)
    )
    entitlement = entitlement_repository.upsert_entitlement(
        EntitlementGrant(
            id=uuid4(),
            user_id=user.id,
            product_code="premium_launch",
            status="active",
            starts_at=issued_at - timedelta(days=1),
            ends_at=issued_at + timedelta(days=30),
            revoked_at=None,
            revoked_reason_code=None,
            created_at=issued_at,
            updated_at=issued_at,
        )
    )

    first = entitlement_repository.append_event(
        EntitlementEvent(
            id=uuid4(),
            entitlement_id=entitlement.id,
            user_id=user.id,
            product_code="premium_launch",
            event_type="grant_activated",
            occurred_at=issued_at,
            reason_code=None,
            provider_name=None,
            provider_event_id=None,
            correlation_id="manual-activation",
        )
    )
    second = entitlement_repository.append_event(
        EntitlementEvent(
            id=uuid4(),
            entitlement_id=entitlement.id,
            user_id=user.id,
            product_code="premium_launch",
            event_type="grant_revoked",
            occurred_at=issued_at + timedelta(hours=1),
            reason_code="support_refund",
            provider_name="stripe",
            provider_event_id="evt_123",
            correlation_id="refund-1",
        )
    )

    events = entitlement_repository.list_entitlement_events(entitlement_id=entitlement.id)

    assert [event.id for event in events] == [second.id, first.id]
    assert events[0].provider_event_id == "evt_123"
    assert events[0].reason_code == "support_refund"
