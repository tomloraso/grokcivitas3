"""phase 19 subject performance gold tables

Revision ID: 2026031139
Revises: 2026031138
Create Date: 2026-03-11 15:00:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031139"
down_revision: str | None = "2026031138"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_ks4_subject_results_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            school_laestab text NULL,
            school_name text NOT NULL,
            old_la_code text NULL,
            new_la_code text NULL,
            la_name text NULL,
            source_version text NOT NULL,
            source_downloaded_at_utc timestamptz NOT NULL,
            establishment_type_group text NULL,
            pupil_count integer NULL,
            qualification_type text NOT NULL,
            qualification_family text NOT NULL,
            qualification_detailed text NULL,
            grade_structure text NOT NULL,
            subject text NOT NULL,
            discount_code text NULL,
            subject_discount_group text NULL,
            grade text NOT NULL,
            number_achieving integer NULL,
            source_file_url text NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (
                urn,
                academic_year,
                qualification_type,
                subject,
                grade,
                source_version
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_ks4_subject_results_yearly_urn
        ON school_ks4_subject_results_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_ks4_subject_results_yearly_year
        ON school_ks4_subject_results_yearly (academic_year)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_ks4_subject_results_yearly_subject
        ON school_ks4_subject_results_yearly (subject, qualification_family)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_16_to_18_subject_results_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            school_laestab text NULL,
            school_name text NOT NULL,
            old_la_code text NULL,
            new_la_code text NULL,
            la_name text NULL,
            source_version text NOT NULL,
            source_downloaded_at_utc timestamptz NOT NULL,
            exam_cohort text NOT NULL,
            qualification_detailed text NOT NULL,
            qualification_family text NOT NULL,
            qualification_level text NULL,
            a_level_equivalent_size numeric(9,2) NULL,
            gcse_equivalent_size numeric(9,2) NULL,
            grade_structure text NOT NULL,
            subject text NOT NULL,
            grade text NOT NULL,
            entries_count integer NULL,
            source_file_url text NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (
                urn,
                academic_year,
                exam_cohort,
                qualification_detailed,
                subject,
                grade,
                source_version
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_16_to_18_subject_results_yearly_urn
        ON school_16_to_18_subject_results_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_16_to_18_subject_results_yearly_year
        ON school_16_to_18_subject_results_yearly (academic_year)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_16_to_18_subject_results_yearly_subject
        ON school_16_to_18_subject_results_yearly (subject, qualification_family, exam_cohort)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_subject_summary_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            key_stage text NOT NULL,
            qualification_family text NOT NULL,
            exam_cohort text NOT NULL DEFAULT '',
            subject text NOT NULL,
            source_version text NOT NULL,
            entries_count_total integer NOT NULL,
            high_grade_count integer NULL,
            high_grade_share_pct numeric(7,4) NULL,
            pass_grade_count integer NULL,
            pass_grade_share_pct numeric(7,4) NULL,
            ranking_eligible boolean NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (
                urn,
                academic_year,
                key_stage,
                qualification_family,
                exam_cohort,
                subject
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_subject_summary_yearly_urn
        ON school_subject_summary_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_subject_summary_yearly_year_stage
        ON school_subject_summary_yearly (academic_year, key_stage)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_subject_summary_yearly_ranking
        ON school_subject_summary_yearly (key_stage, ranking_eligible, subject)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_subject_summary_yearly_ranking")
    op.execute("DROP INDEX IF EXISTS ix_school_subject_summary_yearly_year_stage")
    op.execute("DROP INDEX IF EXISTS ix_school_subject_summary_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_subject_summary_yearly")

    op.execute("DROP INDEX IF EXISTS ix_school_16_to_18_subject_results_yearly_subject")
    op.execute("DROP INDEX IF EXISTS ix_school_16_to_18_subject_results_yearly_year")
    op.execute("DROP INDEX IF EXISTS ix_school_16_to_18_subject_results_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_16_to_18_subject_results_yearly")

    op.execute("DROP INDEX IF EXISTS ix_school_ks4_subject_results_yearly_subject")
    op.execute("DROP INDEX IF EXISTS ix_school_ks4_subject_results_yearly_year")
    op.execute("DROP INDEX IF EXISTS ix_school_ks4_subject_results_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_ks4_subject_results_yearly")
