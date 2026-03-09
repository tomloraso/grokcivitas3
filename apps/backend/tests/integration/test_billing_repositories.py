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

from civitas.application.billing.dto import BillingReconciliationMutation
from civitas.domain.access.models import EntitlementEvent, EntitlementGrant
from civitas.domain.billing.models import (
    BillingCheckoutSession,
    BillingSubscription,
    PaymentCustomer,
    PaymentEvent,
)
from civitas.domain.identity.models import UserAccount
from civitas.infrastructure.config.settings import AppSettings
from civitas.infrastructure.persistence.postgres_billing_state_repository import (
    PostgresBillingStateRepository,
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
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20260309_30_phase_10_payment_checkout_webhooks.py",
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
    reason="Postgres database unavailable for billing repository integration test.",
)


@pytest.fixture()
def engine() -> Engine:
    schema_name = f"test_billing_{uuid4().hex}"
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


def test_billing_migration_creates_expected_tables_and_updates_seed_product(engine: Engine) -> None:
    inspector = inspect(engine)

    assert {
        "payment_customers",
        "checkout_sessions",
        "billing_subscriptions",
        "payment_events",
    }.issubset(set(inspector.get_table_names()))
    assert {index["name"] for index in inspector.get_indexes("payment_customers")} == {
        "ux_payment_customers_provider_customer_id"
    }
    assert {index["name"] for index in inspector.get_indexes("checkout_sessions")} == {
        "ix_checkout_sessions_user_product_status",
        "ux_checkout_sessions_provider_checkout_session_id",
    }
    assert {index["name"] for index in inspector.get_indexes("billing_subscriptions")} == {
        "ix_billing_subscriptions_provider_customer_id",
        "ux_billing_subscriptions_latest_charge_id",
        "ux_billing_subscriptions_provider_subscription_id",
    }
    assert {index["name"] for index in inspector.get_indexes("payment_events")} == {
        "ix_payment_events_user_occurred_at",
        "ux_payment_events_provider_event_id",
    }

    product_repository = PostgresProductRepository(engine=engine)
    product = product_repository.get_product_by_code(code="premium_launch")

    assert product is not None
    assert product.billing_interval == "monthly"
    assert product.provider_price_lookup_key == "premium_launch"


def test_apply_reconciliation_persists_billing_state_and_entitlement_atomically(
    engine: Engine,
) -> None:
    user_repository = PostgresUserRepository(engine=engine)
    billing_repository = PostgresBillingStateRepository(engine=engine)
    now = datetime(2026, 3, 9, 19, 45, tzinfo=timezone.utc)
    user = user_repository.add_user(UserAccount.create(email="premium@example.com", created_at=now))

    mutation = BillingReconciliationMutation(
        payment_event=PaymentEvent(
            id=uuid4(),
            provider_name="stripe",
            provider_event_id="evt_paid_123",
            event_type="invoice.paid",
            effect="invoice_paid",
            occurred_at=now,
            received_at=now,
            payload={"id": "evt_paid_123"},
            signature_verified=True,
            checkout_id=uuid4(),
            user_id=user.id,
            product_code="premium_launch",
            provider_customer_id="cus_test_123",
            provider_checkout_session_id="cs_test_123",
            provider_subscription_id="sub_test_123",
            latest_invoice_id="in_test_123",
            latest_charge_id="ch_test_123",
            reconciliation_status="applied",
            reconciled_at=now,
        ),
        payment_customer=PaymentCustomer(
            user_id=user.id,
            provider_name="stripe",
            provider_customer_id="cus_test_123",
            created_at=now,
            updated_at=now,
        ),
        checkout_session=BillingCheckoutSession(
            id=uuid4(),
            user_id=user.id,
            product_code="premium_launch",
            provider_name="stripe",
            provider_checkout_session_id="cs_test_123",
            provider_customer_id="cus_test_123",
            provider_subscription_id="sub_test_123",
            status="completed",
            checkout_url="https://checkout.stripe.test/session/cs_test_123",
            success_path="/premium/success",
            cancel_path="/premium/cancel",
            requested_at=now - timedelta(minutes=5),
            expires_at=now + timedelta(hours=1),
            completed_at=now,
            canceled_at=None,
            updated_at=now,
        ),
        subscription=BillingSubscription(
            id=uuid4(),
            user_id=user.id,
            product_code="premium_launch",
            provider_name="stripe",
            provider_subscription_id="sub_test_123",
            provider_customer_id="cus_test_123",
            status="active",
            current_period_starts_at=now,
            current_period_ends_at=now + timedelta(days=30),
            cancel_at_period_end=False,
            canceled_at=None,
            latest_checkout_session_id=None,
            entitlement_id=None,
            latest_invoice_id="in_test_123",
            latest_charge_id="ch_test_123",
            created_at=now,
            updated_at=now,
        ),
        entitlement=EntitlementGrant(
            id=uuid4(),
            user_id=user.id,
            product_code="premium_launch",
            status="active",
            starts_at=now,
            ends_at=now + timedelta(days=30),
            revoked_at=None,
            revoked_reason_code=None,
            created_at=now,
            updated_at=now,
        ),
        entitlement_event=EntitlementEvent(
            id=uuid4(),
            entitlement_id=uuid4(),
            user_id=user.id,
            product_code="premium_launch",
            event_type="grant_activated",
            occurred_at=now,
            reason_code=None,
            provider_name="stripe",
            provider_event_id="evt_paid_123",
            correlation_id="sub_test_123",
        ),
    )

    # Keep the entitlement event pointing at the persisted entitlement row.
    mutation = BillingReconciliationMutation(
        payment_event=mutation.payment_event,
        payment_customer=mutation.payment_customer,
        checkout_session=mutation.checkout_session,
        subscription=mutation.subscription,
        entitlement=mutation.entitlement,
        entitlement_event=EntitlementEvent(
            id=uuid4(),
            entitlement_id=mutation.entitlement.id,
            user_id=user.id,
            product_code="premium_launch",
            event_type="grant_activated",
            occurred_at=now,
            reason_code=None,
            provider_name="stripe",
            provider_event_id="evt_paid_123",
            correlation_id="sub_test_123",
        ),
    )

    assert billing_repository.apply_reconciliation(mutation) is True
    assert billing_repository.apply_reconciliation(mutation) is False

    payment_customer = billing_repository.get_payment_customer_by_user(
        user_id=user.id,
        provider_name="stripe",
    )
    checkout = billing_repository.get_checkout_session_by_provider_checkout_session_id(
        provider_name="stripe",
        provider_checkout_session_id="cs_test_123",
    )
    subscription = billing_repository.get_subscription_by_provider_subscription_id(
        provider_name="stripe",
        provider_subscription_id="sub_test_123",
    )

    assert payment_customer is not None
    assert payment_customer.provider_customer_id == "cus_test_123"
    assert checkout is not None
    assert checkout.status == "completed"
    assert subscription is not None
    assert subscription.latest_charge_id == "ch_test_123"

    with engine.connect() as connection:
        entitlement_count = connection.execute(
            text("SELECT COUNT(*) FROM entitlements")
        ).scalar_one()
        event_count = connection.execute(
            text("SELECT COUNT(*) FROM payment_events WHERE provider_event_id = 'evt_paid_123'")
        ).scalar_one()

    assert entitlement_count == 1
    assert event_count == 1
