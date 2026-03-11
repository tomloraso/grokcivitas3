"""phase 18 school leaver destinations yearly

Revision ID: 2026031138
Revises: 2026031037
Create Date: 2026-03-11 10:30:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031138"
down_revision: str | None = "2026031037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_leaver_destinations_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            destination_stage text NOT NULL,
            qualification_group text NOT NULL DEFAULT '',
            qualification_level text NOT NULL DEFAULT '',
            breakdown_topic text NOT NULL,
            breakdown text NOT NULL,
            school_name text NOT NULL,
            school_laestab text NULL,
            admission_policy text NULL,
            entry_gender text NULL,
            institution_group text NULL,
            institution_type text NULL,
            cohort_count integer NULL,
            overall_count integer NULL,
            overall_pct numeric(7,4) NULL,
            education_count integer NULL,
            education_pct numeric(7,4) NULL,
            apprenticeship_count integer NULL,
            apprenticeship_pct numeric(7,4) NULL,
            employment_count integer NULL,
            employment_pct numeric(7,4) NULL,
            not_sustained_count integer NULL,
            not_sustained_pct numeric(7,4) NULL,
            activity_unknown_count integer NULL,
            activity_unknown_pct numeric(7,4) NULL,
            fe_count integer NULL,
            fe_pct numeric(7,4) NULL,
            other_education_count integer NULL,
            other_education_pct numeric(7,4) NULL,
            school_sixth_form_count integer NULL,
            school_sixth_form_pct numeric(7,4) NULL,
            sixth_form_college_count integer NULL,
            sixth_form_college_pct numeric(7,4) NULL,
            higher_education_count integer NULL,
            higher_education_pct numeric(7,4) NULL,
            source_file_url text NOT NULL,
            source_updated_at_utc timestamptz NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (
                urn,
                academic_year,
                destination_stage,
                qualification_group,
                qualification_level,
                breakdown_topic,
                breakdown
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_leaver_destinations_yearly_urn
        ON school_leaver_destinations_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_leaver_destinations_yearly_academic_year
        ON school_leaver_destinations_yearly (academic_year)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_leaver_destinations_yearly_stage
        ON school_leaver_destinations_yearly (destination_stage)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_leaver_destinations_yearly_breakdown
        ON school_leaver_destinations_yearly (
            breakdown_topic,
            breakdown,
            qualification_group,
            qualification_level
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_leaver_destinations_yearly_breakdown")
    op.execute("DROP INDEX IF EXISTS ix_school_leaver_destinations_yearly_stage")
    op.execute("DROP INDEX IF EXISTS ix_school_leaver_destinations_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_leaver_destinations_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_leaver_destinations_yearly")
