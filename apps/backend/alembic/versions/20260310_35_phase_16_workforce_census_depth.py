"""phase 16 workforce census depth

Revision ID: 2026031035
Revises: 2026031034
Create Date: 2026-03-10 18:45:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031035"
down_revision: str | None = "2026031034"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

WORKFORCE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("teacher_headcount_total", "double precision"),
    ("teacher_fte_total", "double precision"),
    ("headteacher_headcount", "double precision"),
    ("deputy_headteacher_headcount", "double precision"),
    ("assistant_headteacher_headcount", "double precision"),
    ("classroom_teacher_headcount", "double precision"),
    ("leadership_headcount", "double precision"),
    ("leadership_share_of_teachers", "double precision"),
    ("teacher_female_pct", "double precision"),
    ("teacher_male_pct", "double precision"),
    ("teacher_qts_pct", "double precision"),
    ("teacher_unqualified_pct", "double precision"),
    ("support_staff_headcount_total", "double precision"),
    ("support_staff_fte_total", "double precision"),
    ("teaching_assistant_headcount", "double precision"),
    ("teaching_assistant_fte", "double precision"),
    ("administrative_staff_headcount", "double precision"),
    ("auxiliary_staff_headcount", "double precision"),
    ("school_business_professional_headcount", "double precision"),
    ("leadership_non_teacher_headcount", "double precision"),
    ("teacher_average_mean_salary_gbp", "double precision"),
    ("teacher_average_median_salary_gbp", "double precision"),
    ("teachers_on_leadership_pay_range_pct", "double precision"),
    ("teacher_absence_pct", "double precision"),
    ("teacher_absence_days_total", "double precision"),
    ("teacher_absence_days_average", "double precision"),
    ("teacher_absence_days_average_all_teachers", "double precision"),
    ("teacher_vacancy_count", "double precision"),
    ("teacher_vacancy_rate", "double precision"),
    ("teacher_tempfilled_vacancy_count", "double precision"),
    ("teacher_tempfilled_vacancy_rate", "double precision"),
    ("third_party_support_staff_headcount", "double precision"),
)


def upgrade() -> None:
    for column_name, column_type in WORKFORCE_COLUMNS:
        op.execute(
            f"""
            ALTER TABLE school_workforce_yearly
            ADD COLUMN IF NOT EXISTS {column_name} {column_type} NULL
            """
        )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_teacher_characteristics_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            characteristic_group text NOT NULL,
            characteristic text NOT NULL,
            grade text NULL,
            sex text NULL,
            age_group text NULL,
            working_pattern text NULL,
            qts_status text NULL,
            on_route text NULL,
            ethnicity_major text NULL,
            teacher_fte double precision NULL,
            teacher_headcount double precision NULL,
            teacher_fte_pct double precision NULL,
            teacher_headcount_pct double precision NULL,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year, characteristic_group, characteristic)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_teacher_characteristics_yearly_urn
        ON school_teacher_characteristics_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_teacher_characteristics_yearly_academic_year
        ON school_teacher_characteristics_yearly (academic_year)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_teacher_characteristics_yearly_group
        ON school_teacher_characteristics_yearly (characteristic_group)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_support_staff_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            post text NOT NULL,
            sex text NOT NULL,
            ethnicity_major text NOT NULL,
            support_staff_fte double precision NULL,
            support_staff_headcount double precision NULL,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year, post, sex, ethnicity_major)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_support_staff_yearly_urn
        ON school_support_staff_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_support_staff_yearly_academic_year
        ON school_support_staff_yearly (academic_year)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_support_staff_yearly_post
        ON school_support_staff_yearly (post)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_support_staff_yearly_post")
    op.execute("DROP INDEX IF EXISTS ix_school_support_staff_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_support_staff_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_support_staff_yearly")

    op.execute("DROP INDEX IF EXISTS ix_school_teacher_characteristics_yearly_group")
    op.execute("DROP INDEX IF EXISTS ix_school_teacher_characteristics_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_teacher_characteristics_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_teacher_characteristics_yearly")

    for column_name, _column_type in reversed(WORKFORCE_COLUMNS):
        op.execute(
            f"""
            ALTER TABLE school_workforce_yearly
            DROP COLUMN IF EXISTS {column_name}
            """
        )
