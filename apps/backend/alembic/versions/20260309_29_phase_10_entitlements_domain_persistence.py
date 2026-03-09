"""phase 10 entitlements domain and persistence

Revision ID: 2026030929
Revises: 2026030931
Create Date: 2026-03-09 14:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030929"
down_revision: str | None = "2026030931"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "premium_products",
        sa.Column("code", sa.String(length=100), primary_key=True, nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("billing_interval", sa.String(length=32), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("provider_price_lookup_key", sa.String(length=255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
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
        "ck_premium_products_billing_interval",
        "premium_products",
        "billing_interval IS NULL OR billing_interval IN ('monthly', 'annual', 'one_time')",
    )

    op.create_table(
        "product_capabilities",
        sa.Column(
            "product_code",
            sa.String(length=100),
            sa.ForeignKey("premium_products.code", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("capability_key", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_index(
        "ix_product_capabilities_capability_key",
        "product_capabilities",
        ["capability_key"],
        unique=False,
    )

    op.create_table(
        "entitlements",
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
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason_code", sa.String(length=64), nullable=True),
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
        "ck_entitlements_status",
        "entitlements",
        "status IN ('pending', 'active', 'revoked')",
    )
    op.create_index(
        "ix_entitlements_user_status_ends_at",
        "entitlements",
        ["user_id", "status", "ends_at"],
        unique=False,
    )
    op.create_index(
        "ix_entitlements_user_product_code",
        "entitlements",
        ["user_id", "product_code"],
        unique=False,
    )

    op.create_table(
        "entitlement_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "entitlement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entitlements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_code", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("provider_name", sa.String(length=64), nullable=True),
        sa.Column("provider_event_id", sa.String(length=255), nullable=True),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_index(
        "ix_entitlement_events_entitlement_occurred_at",
        "entitlement_events",
        ["entitlement_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_entitlement_events_user_occurred_at",
        "entitlement_events",
        ["user_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_entitlement_events_provider_event_ref",
        "entitlement_events",
        ["provider_name", "provider_event_id"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO premium_products (
            code,
            display_name,
            description,
            billing_interval,
            duration_days,
            provider_price_lookup_key,
            is_active,
            created_at,
            updated_at
        ) VALUES (
            'premium_launch',
            'Premium',
            'Launch premium bundle for analyst, compare, and neighbourhood access.',
            NULL,
            NULL,
            NULL,
            TRUE,
            timezone('utc', now()),
            timezone('utc', now())
        )
        ON CONFLICT (code) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            description = EXCLUDED.description,
            billing_interval = EXCLUDED.billing_interval,
            duration_days = EXCLUDED.duration_days,
            provider_price_lookup_key = EXCLUDED.provider_price_lookup_key,
            is_active = EXCLUDED.is_active,
            updated_at = timezone('utc', now())
        """
    )
    for capability_key in (
        "premium_ai_analyst",
        "premium_comparison",
        "premium_neighbourhood",
    ):
        op.execute(
            f"""
            INSERT INTO product_capabilities (product_code, capability_key, created_at)
            VALUES ('premium_launch', '{capability_key}', timezone('utc', now()))
            ON CONFLICT (product_code, capability_key) DO NOTHING
            """
        )


def downgrade() -> None:
    op.drop_index("ix_entitlement_events_provider_event_ref", table_name="entitlement_events")
    op.drop_index("ix_entitlement_events_user_occurred_at", table_name="entitlement_events")
    op.drop_index(
        "ix_entitlement_events_entitlement_occurred_at",
        table_name="entitlement_events",
    )
    op.drop_table("entitlement_events")
    op.drop_index("ix_entitlements_user_product_code", table_name="entitlements")
    op.drop_index("ix_entitlements_user_status_ends_at", table_name="entitlements")
    op.drop_constraint("ck_entitlements_status", "entitlements", type_="check")
    op.drop_table("entitlements")
    op.drop_index("ix_product_capabilities_capability_key", table_name="product_capabilities")
    op.drop_table("product_capabilities")
    op.drop_constraint("ck_premium_products_billing_interval", "premium_products", type_="check")
    op.drop_table("premium_products")
