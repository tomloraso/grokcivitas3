"""phase2 ofsted inspections timeline table

Revision ID: 2026030206
Revises: 2026030205
Create Date: 2026-03-02 20:00:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030206"
down_revision: str | None = "2026030205"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ofsted_inspections (
            inspection_number text PRIMARY KEY,
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            inspection_start_date date NOT NULL,
            inspection_end_date date NULL,
            publication_date date NULL,
            inspection_type text NULL,
            inspection_type_grouping text NULL,
            event_type_grouping text NULL,
            overall_effectiveness_code text NULL,
            overall_effectiveness_label text NULL,
            headline_outcome_text text NULL,
            category_of_concern text NULL,
            source_schema_version text NOT NULL,
            source_asset_url text NOT NULL,
            source_asset_month text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_ofsted_inspections_urn_inspection_start_date "
        "ON ofsted_inspections (urn, inspection_start_date DESC)"
    )
    op.execute(
        "CREATE INDEX ix_ofsted_inspections_publication_date "
        "ON ofsted_inspections (publication_date)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_ofsted_inspections_publication_date")
    op.execute("DROP INDEX IF EXISTS ix_ofsted_inspections_urn_inspection_start_date")
    op.execute("DROP TABLE IF EXISTS ofsted_inspections")
