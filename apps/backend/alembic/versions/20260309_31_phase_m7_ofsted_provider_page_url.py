"""phase m7 ofsted provider page url

Revision ID: 2026030931
Revises: 2026030828
Create Date: 2026-03-09 21:15:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030931"
down_revision: str | None = "2026030828"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE school_ofsted_latest ADD COLUMN IF NOT EXISTS provider_page_url text NULL"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS provider_page_url")
