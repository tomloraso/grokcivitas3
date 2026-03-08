"""phase 11 search summary projection

Revision ID: 2026030828
Revises: 2026030827
Create Date: 2026-03-08 19:45:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030828"
down_revision: str | None = "2026030827"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_search_summary (
            urn text PRIMARY KEY REFERENCES schools(urn) ON DELETE CASCADE,
            name text NOT NULL,
            phase text NULL,
            type text NULL,
            postcode text NULL,
            location geography(Point, 4326) NOT NULL,
            pupil_count integer NULL,
            latest_ofsted_label text NULL,
            latest_ofsted_sort_rank integer NULL,
            latest_ofsted_availability text NOT NULL,
            primary_academic_metric_key text NULL,
            primary_academic_metric_label text NULL,
            primary_academic_metric_value double precision NULL,
            primary_academic_metric_availability text NOT NULL,
            secondary_academic_metric_key text NULL,
            secondary_academic_metric_label text NULL,
            secondary_academic_metric_value double precision NULL,
            secondary_academic_metric_availability text NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_school_search_summary_location "
        "ON school_search_summary USING GIST (location)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_school_search_summary_latest_ofsted_sort_rank "
        "ON school_search_summary (latest_ofsted_sort_rank)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_school_search_summary_primary_metric_value "
        "ON school_search_summary (primary_academic_metric_value)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_school_search_summary_secondary_metric_value "
        "ON school_search_summary (secondary_academic_metric_value)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_search_summary_secondary_metric_value")
    op.execute("DROP INDEX IF EXISTS ix_school_search_summary_primary_metric_value")
    op.execute("DROP INDEX IF EXISTS ix_school_search_summary_latest_ofsted_sort_rank")
    op.execute("DROP INDEX IF EXISTS ix_school_search_summary_location")
    op.execute("DROP TABLE IF EXISTS school_search_summary")
