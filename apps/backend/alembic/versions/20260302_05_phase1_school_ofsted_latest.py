"""phase1 school ofsted latest table

Revision ID: 2026030205
Revises: 2026030204
Create Date: 2026-03-02 16:00:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030205"
down_revision: str | None = "2026030204"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE school_ofsted_latest (
            urn text PRIMARY KEY REFERENCES schools(urn) ON DELETE CASCADE,
            inspection_start_date date NULL,
            publication_date date NULL,
            overall_effectiveness_code text NULL,
            overall_effectiveness_label text NULL,
            is_graded boolean NOT NULL DEFAULT false,
            ungraded_outcome text NULL,
            source_asset_url text NOT NULL,
            source_asset_month text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_school_ofsted_latest_overall_effectiveness_code "
        "ON school_ofsted_latest (overall_effectiveness_code)"
    )
    op.execute(
        "CREATE INDEX ix_school_ofsted_latest_inspection_start_date "
        "ON school_ofsted_latest (inspection_start_date)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_ofsted_latest_inspection_start_date")
    op.execute("DROP INDEX IF EXISTS ix_school_ofsted_latest_overall_effectiveness_code")
    op.execute("DROP TABLE IF EXISTS school_ofsted_latest")
