"""phase1 school demographics yearly table

Revision ID: 2026030204
Revises: 2026022803
Create Date: 2026-03-02 12:00:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030204"
down_revision: str | None = "2026022803"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE school_demographics_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            disadvantaged_pct double precision NULL,
            fsm_pct double precision NULL,
            sen_pct double precision NULL,
            sen_support_pct double precision NULL,
            ehcp_pct double precision NULL,
            eal_pct double precision NULL,
            first_language_english_pct double precision NULL,
            first_language_unclassified_pct double precision NULL,
            total_pupils integer NULL,
            has_ethnicity_data boolean NOT NULL DEFAULT false,
            has_top_languages_data boolean NOT NULL DEFAULT false,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year)
        )
        """
    )
    op.execute("CREATE INDEX ix_school_demographics_yearly_urn ON school_demographics_yearly (urn)")
    op.execute(
        "CREATE INDEX ix_school_demographics_yearly_academic_year "
        "ON school_demographics_yearly (academic_year)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_demographics_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_demographics_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_demographics_yearly")
