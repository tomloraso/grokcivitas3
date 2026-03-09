"""phase 10 payment checkout and webhooks

Revision ID: 2026030930
Revises: 2026030929
Create Date: 2026-03-09 18:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030930"
down_revision: str | None = "2026030929"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payment_customers",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.PrimaryKeyConstraint("provider_name", "user_id"),
    )
    op.create_index(
        "ux_payment_customers_provider_customer_id",
        "payment_customers",
        ["provider_name", "provider_customer_id"],
        unique=True,
    )

    op.create_table(
        "checkout_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_code",
            sa.String(length=100),
            sa.ForeignKey("premium_products.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_checkout_session_id", sa.String(length=255), nullable=True),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("checkout_url", sa.Text(), nullable=True),
        sa.Column("success_path", sa.String(length=2048), nullable=False),
        sa.Column("cancel_path", sa.String(length=2048), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_check_constraint(
        "ck_checkout_sessions_status",
        "checkout_sessions",
        "status IN ('pending_provider', 'open', 'completed', 'expired', 'canceled', 'failed')",
    )
    op.create_index(
        "ix_checkout_sessions_user_product_status",
        "checkout_sessions",
        ["user_id", "product_code", "status", "requested_at"],
        unique=False,
    )
    op.create_index(
        "ux_checkout_sessions_provider_checkout_session_id",
        "checkout_sessions",
        ["provider_name", "provider_checkout_session_id"],
        unique=True,
        postgresql_where=sa.text("provider_checkout_session_id IS NOT NULL"),
    )

    op.create_table(
        "billing_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_code",
            sa.String(length=100),
            sa.ForeignKey("premium_products.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=False),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_period_starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cancel_at_period_end",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "latest_checkout_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("checkout_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "entitlement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entitlements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("latest_invoice_id", sa.String(length=255), nullable=True),
        sa.Column("latest_charge_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_check_constraint(
        "ck_billing_subscriptions_status",
        "billing_subscriptions",
        "status IN ('incomplete', 'incomplete_expired', 'trialing', 'active', "
        "'past_due', 'canceled', 'unpaid', 'paused')",
    )
    op.create_index(
        "ux_billing_subscriptions_provider_subscription_id",
        "billing_subscriptions",
        ["provider_name", "provider_subscription_id"],
        unique=True,
    )
    op.create_index(
        "ix_billing_subscriptions_provider_customer_id",
        "billing_subscriptions",
        ["provider_name", "provider_customer_id", "updated_at"],
        unique=False,
    )
    op.create_index(
        "ux_billing_subscriptions_latest_charge_id",
        "billing_subscriptions",
        ["provider_name", "latest_charge_id"],
        unique=True,
        postgresql_where=sa.text("latest_charge_id IS NOT NULL"),
    )

    op.create_table(
        "payment_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("effect", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("signature_verified", sa.Boolean(), nullable=False),
        sa.Column("checkout_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_code", sa.String(length=100), nullable=True),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=True),
        sa.Column("provider_checkout_session_id", sa.String(length=255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("latest_invoice_id", sa.String(length=255), nullable=True),
        sa.Column("latest_charge_id", sa.String(length=255), nullable=True),
        sa.Column("reconciliation_status", sa.String(length=32), nullable=False),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_check_constraint(
        "ck_payment_events_reconciliation_status",
        "payment_events",
        "reconciliation_status IN ('pending', 'applied', 'duplicate', 'ignored', 'failed')",
    )
    op.create_index(
        "ux_payment_events_provider_event_id",
        "payment_events",
        ["provider_name", "provider_event_id"],
        unique=True,
    )
    op.create_index(
        "ix_payment_events_user_occurred_at",
        "payment_events",
        ["user_id", "occurred_at"],
        unique=False,
    )

    op.execute(
        """
        UPDATE premium_products
        SET
            billing_interval = 'monthly',
            provider_price_lookup_key = 'premium_launch',
            updated_at = timezone('utc', now())
        WHERE code = 'premium_launch'
        """
    )


def downgrade() -> None:
    op.drop_index("ix_payment_events_user_occurred_at", table_name="payment_events")
    op.drop_index("ux_payment_events_provider_event_id", table_name="payment_events")
    op.drop_constraint(
        "ck_payment_events_reconciliation_status",
        "payment_events",
        type_="check",
    )
    op.drop_table("payment_events")
    op.drop_index(
        "ux_billing_subscriptions_latest_charge_id",
        table_name="billing_subscriptions",
    )
    op.drop_index(
        "ix_billing_subscriptions_provider_customer_id",
        table_name="billing_subscriptions",
    )
    op.drop_index(
        "ux_billing_subscriptions_provider_subscription_id",
        table_name="billing_subscriptions",
    )
    op.drop_constraint(
        "ck_billing_subscriptions_status",
        "billing_subscriptions",
        type_="check",
    )
    op.drop_table("billing_subscriptions")
    op.drop_index(
        "ux_checkout_sessions_provider_checkout_session_id",
        table_name="checkout_sessions",
    )
    op.drop_index("ix_checkout_sessions_user_product_status", table_name="checkout_sessions")
    op.drop_constraint("ck_checkout_sessions_status", "checkout_sessions", type_="check")
    op.drop_table("checkout_sessions")
    op.drop_index(
        "ux_payment_customers_provider_customer_id",
        table_name="payment_customers",
    )
    op.drop_table("payment_customers")
