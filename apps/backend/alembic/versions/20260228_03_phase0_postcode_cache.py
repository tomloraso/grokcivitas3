"""phase0 postcode cache table

Revision ID: 2026022803
Revises: 2026022702
Create Date: 2026-02-28 00:30:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026022803"
down_revision: str | None = "2026022702"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE postcode_cache (
            postcode text PRIMARY KEY,
            lat double precision NOT NULL,
            lng double precision NOT NULL,
            lsoa text NULL,
            admin_district text NULL,
            cached_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute("CREATE INDEX ix_postcode_cache_cached_at ON postcode_cache (cached_at)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_postcode_cache_cached_at")
    op.execute("DROP TABLE IF EXISTS postcode_cache")
