"""phase m3 attendance behaviour

Revision ID: 2026030516
Revises: 2026030515
Create Date: 2026-03-05 16:10:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030516"
down_revision: str | None = "2026030515"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_attendance_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            overall_attendance_pct double precision NULL,
            overall_absence_pct double precision NULL,
            persistent_absence_pct double precision NULL,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_attendance_yearly_urn
        ON school_attendance_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_attendance_yearly_academic_year
        ON school_attendance_yearly (academic_year)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_behaviour_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            suspensions_count integer NULL,
            suspensions_rate double precision NULL,
            permanent_exclusions_count integer NULL,
            permanent_exclusions_rate double precision NULL,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_behaviour_yearly_urn
        ON school_behaviour_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_behaviour_yearly_academic_year
        ON school_behaviour_yearly (academic_year)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_behaviour_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_behaviour_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_behaviour_yearly")

    op.execute("DROP INDEX IF EXISTS ix_school_attendance_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_attendance_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_attendance_yearly")
