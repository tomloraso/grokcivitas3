"""phase m4 workforce leadership

Revision ID: 2026030517
Revises: 2026030516
Create Date: 2026-03-05 19:15:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030517"
down_revision: str | None = "2026030516"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_workforce_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            pupil_teacher_ratio double precision NULL,
            supply_staff_pct double precision NULL,
            teachers_3plus_years_pct double precision NULL,
            teacher_turnover_pct double precision NULL,
            qts_pct double precision NULL,
            qualifications_level6_plus_pct double precision NULL,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_workforce_yearly_urn
        ON school_workforce_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_workforce_yearly_academic_year
        ON school_workforce_yearly (academic_year)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_leadership_snapshot (
            urn text PRIMARY KEY REFERENCES schools(urn) ON DELETE CASCADE,
            headteacher_name text NULL,
            headteacher_start_date date NULL,
            headteacher_tenure_years double precision NULL,
            leadership_turnover_score double precision NULL,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_leadership_snapshot_headteacher_start_date
        ON school_leadership_snapshot (headteacher_start_date)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_leadership_snapshot_headteacher_start_date")
    op.execute("DROP TABLE IF EXISTS school_leadership_snapshot")

    op.execute("DROP INDEX IF EXISTS ix_school_workforce_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_workforce_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_workforce_yearly")
