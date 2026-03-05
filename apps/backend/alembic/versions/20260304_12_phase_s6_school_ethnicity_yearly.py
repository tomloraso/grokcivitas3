"""phase s6 school ethnicity yearly table

Revision ID: 2026030412
Revises: 2026030311
Create Date: 2026-03-04 16:00:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030412"
down_revision: str | None = "2026030311"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE school_ethnicity_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            white_british_pct double precision NULL,
            white_british_count integer NULL,
            irish_pct double precision NULL,
            irish_count integer NULL,
            traveller_of_irish_heritage_pct double precision NULL,
            traveller_of_irish_heritage_count integer NULL,
            any_other_white_background_pct double precision NULL,
            any_other_white_background_count integer NULL,
            gypsy_roma_pct double precision NULL,
            gypsy_roma_count integer NULL,
            white_and_black_caribbean_pct double precision NULL,
            white_and_black_caribbean_count integer NULL,
            white_and_black_african_pct double precision NULL,
            white_and_black_african_count integer NULL,
            white_and_asian_pct double precision NULL,
            white_and_asian_count integer NULL,
            any_other_mixed_background_pct double precision NULL,
            any_other_mixed_background_count integer NULL,
            indian_pct double precision NULL,
            indian_count integer NULL,
            pakistani_pct double precision NULL,
            pakistani_count integer NULL,
            bangladeshi_pct double precision NULL,
            bangladeshi_count integer NULL,
            any_other_asian_background_pct double precision NULL,
            any_other_asian_background_count integer NULL,
            caribbean_pct double precision NULL,
            caribbean_count integer NULL,
            african_pct double precision NULL,
            african_count integer NULL,
            any_other_black_background_pct double precision NULL,
            any_other_black_background_count integer NULL,
            chinese_pct double precision NULL,
            chinese_count integer NULL,
            any_other_ethnic_group_pct double precision NULL,
            any_other_ethnic_group_count integer NULL,
            unclassified_pct double precision NULL,
            unclassified_count integer NULL,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year)
        )
        """
    )
    op.execute("CREATE INDEX ix_school_ethnicity_yearly_urn ON school_ethnicity_yearly (urn)")
    op.execute(
        "CREATE INDEX ix_school_ethnicity_yearly_academic_year "
        "ON school_ethnicity_yearly (academic_year)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_ethnicity_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_ethnicity_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_ethnicity_yearly")
