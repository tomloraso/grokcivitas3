"""phase 14 favourites foundation

Revision ID: 2026031032
Revises: 2026030931
Create Date: 2026-03-10 10:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031032"
down_revision: str | None = "2026030931"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_schools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("school_urn", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_foreign_key(
        "fk_saved_schools_school_urn",
        "saved_schools",
        "schools",
        ["school_urn"],
        ["urn"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ux_saved_schools_user_school_urn",
        "saved_schools",
        ["user_id", "school_urn"],
        unique=True,
    )
    op.create_index(
        "ix_saved_schools_user_created_at",
        "saved_schools",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "saved_school_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("school_urn", sa.Text(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_check_constraint(
        "ck_saved_school_events_event_type",
        "saved_school_events",
        "event_type IN ('saved', 'removed')",
    )
    op.create_index(
        "ix_saved_school_events_user_occurred_at",
        "saved_school_events",
        ["user_id", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_saved_school_events_user_occurred_at", table_name="saved_school_events")
    op.drop_constraint(
        "ck_saved_school_events_event_type",
        "saved_school_events",
        type_="check",
    )
    op.drop_table("saved_school_events")
    op.drop_index("ix_saved_schools_user_created_at", table_name="saved_schools")
    op.drop_index("ux_saved_schools_user_school_urn", table_name="saved_schools")
    op.drop_constraint(
        "fk_saved_schools_school_urn",
        "saved_schools",
        type_="foreignkey",
    )
    op.drop_table("saved_schools")
