"""phase m2 demographics support depth

Revision ID: 2026030515
Revises: 2026030514
Create Date: 2026-03-05 12:10:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030515"
down_revision: str | None = "2026030514"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE school_demographics_yearly "
        "ADD COLUMN IF NOT EXISTS fsm6_pct double precision NULL"
    )
    op.execute(
        "ALTER TABLE school_demographics_yearly "
        "ADD COLUMN IF NOT EXISTS male_pct double precision NULL"
    )
    op.execute(
        "ALTER TABLE school_demographics_yearly "
        "ADD COLUMN IF NOT EXISTS female_pct double precision NULL"
    )
    op.execute(
        "ALTER TABLE school_demographics_yearly "
        "ADD COLUMN IF NOT EXISTS pupil_mobility_pct double precision NULL"
    )
    op.execute(
        "ALTER TABLE school_demographics_yearly "
        "ADD COLUMN IF NOT EXISTS has_fsm6_data boolean NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE school_demographics_yearly "
        "ADD COLUMN IF NOT EXISTS has_gender_data boolean NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE school_demographics_yearly "
        "ADD COLUMN IF NOT EXISTS has_mobility_data boolean NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE school_demographics_yearly "
        "ADD COLUMN IF NOT EXISTS has_send_primary_need_data boolean NOT NULL DEFAULT false"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_send_primary_need_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            need_key text NOT NULL,
            need_label text NOT NULL,
            pupil_count integer NULL,
            percentage double precision NULL,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year, need_key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_send_primary_need_yearly_urn
        ON school_send_primary_need_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_send_primary_need_yearly_academic_year
        ON school_send_primary_need_yearly (academic_year)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_home_language_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            language_key text NOT NULL,
            language_label text NOT NULL,
            rank integer NOT NULL,
            pupil_count integer NULL,
            percentage double precision NULL,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year, language_key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_home_language_yearly_urn
        ON school_home_language_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_home_language_yearly_academic_year
        ON school_home_language_yearly (academic_year)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_home_language_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_home_language_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_home_language_yearly")

    op.execute("DROP INDEX IF EXISTS ix_school_send_primary_need_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_send_primary_need_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_send_primary_need_yearly")

    op.execute(
        "ALTER TABLE school_demographics_yearly DROP COLUMN IF EXISTS has_send_primary_need_data"
    )
    op.execute("ALTER TABLE school_demographics_yearly DROP COLUMN IF EXISTS has_mobility_data")
    op.execute("ALTER TABLE school_demographics_yearly DROP COLUMN IF EXISTS has_gender_data")
    op.execute("ALTER TABLE school_demographics_yearly DROP COLUMN IF EXISTS has_fsm6_data")
    op.execute("ALTER TABLE school_demographics_yearly DROP COLUMN IF EXISTS pupil_mobility_pct")
    op.execute("ALTER TABLE school_demographics_yearly DROP COLUMN IF EXISTS female_pct")
    op.execute("ALTER TABLE school_demographics_yearly DROP COLUMN IF EXISTS male_pct")
    op.execute("ALTER TABLE school_demographics_yearly DROP COLUMN IF EXISTS fsm6_pct")
