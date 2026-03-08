"""phase 10 auth pkce hardening

Revision ID: 2026030827
Revises: 2026030726
Create Date: 2026-03-08 11:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030827"
down_revision: str | None = "2026030726"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_attempts",
        sa.Column("attempt_id", sa.String(length=255), primary_key=True, nullable=False),
        sa.Column("return_to", sa.String(length=2048), nullable=False),
        sa.Column("code_verifier", sa.String(length=255), nullable=False),
        sa.Column(
            "issued_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_auth_attempts_expires_at", "auth_attempts", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_auth_attempts_expires_at", table_name="auth_attempts")
    op.drop_table("auth_attempts")
