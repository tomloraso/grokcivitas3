"""phase 17 gias join keys

Revision ID: 2026031036
Revises: 2026031035
Create Date: 2026-03-10 18:00:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031036"
down_revision: str | None = "2026031035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS establishment_number text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS school_laestab text NULL")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_schools_school_laestab
        ON schools (school_laestab)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_schools_school_laestab")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS school_laestab")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS establishment_number")
