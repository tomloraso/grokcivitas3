"""phase0 gias schools table

Revision ID: 2026022702
Revises: 2026022701
Create Date: 2026-02-27 00:30:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026022702"
down_revision: str | None = "2026022701"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE schools (
            urn text PRIMARY KEY,
            name text NOT NULL,
            phase text NULL,
            type text NULL,
            status text NULL,
            postcode text NULL,
            easting double precision NOT NULL,
            northing double precision NOT NULL,
            location geography(Point, 4326) NOT NULL,
            capacity integer NULL,
            pupil_count integer NULL,
            open_date date NULL,
            close_date date NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute("CREATE INDEX ix_schools_location ON schools USING GIST (location)")
    op.execute("CREATE INDEX ix_schools_status ON schools (status)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_schools_status")
    op.execute("DROP INDEX IF EXISTS ix_schools_location")
    op.execute("DROP TABLE IF EXISTS schools")
