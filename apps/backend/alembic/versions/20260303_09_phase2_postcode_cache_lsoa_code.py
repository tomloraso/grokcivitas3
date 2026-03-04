"""phase2 postcode cache lsoa code

Revision ID: 2026030309
Revises: 2026030208
Create Date: 2026-03-03 03:00:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030309"
down_revision: str | None = "2026030208"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE postcode_cache ADD COLUMN IF NOT EXISTS lsoa_code text NULL")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_postcode_cache_lsoa_code ON postcode_cache (lsoa_code)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_postcode_cache_lsoa_code")
    op.execute("ALTER TABLE postcode_cache DROP COLUMN IF EXISTS lsoa_code")
