"""phase2 area crime context table

Revision ID: 2026030208
Revises: 2026030207
Create Date: 2026-03-02 23:10:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030208"
down_revision: str | None = "2026030207"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE area_crime_context (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            month date NOT NULL,
            crime_category text NOT NULL,
            incident_count integer NOT NULL,
            radius_meters double precision NOT NULL,
            source_month text NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, month, crime_category, radius_meters)
        )
        """
    )
    op.execute("CREATE INDEX ix_area_crime_context_urn_month ON area_crime_context (urn, month)")
    op.execute(
        "CREATE INDEX ix_area_crime_context_month_category ON area_crime_context (month, crime_category)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_area_crime_context_month_category")
    op.execute("DROP INDEX IF EXISTS ix_area_crime_context_urn_month")
    op.execute("DROP TABLE IF EXISTS area_crime_context")
