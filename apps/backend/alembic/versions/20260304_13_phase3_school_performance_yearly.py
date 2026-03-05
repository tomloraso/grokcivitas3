"""phase 3 school performance yearly table

Revision ID: 2026030413
Revises: 2026030412
Create Date: 2026-03-04 17:10:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030413"
down_revision: str | None = "2026030412"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_performance_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            attainment8_average double precision NULL,
            progress8_average double precision NULL,
            progress8_disadvantaged double precision NULL,
            progress8_not_disadvantaged double precision NULL,
            progress8_disadvantaged_gap double precision NULL,
            engmath_5_plus_pct double precision NULL,
            engmath_4_plus_pct double precision NULL,
            ebacc_entry_pct double precision NULL,
            ebacc_5_plus_pct double precision NULL,
            ebacc_4_plus_pct double precision NULL,
            ks2_reading_expected_pct double precision NULL,
            ks2_writing_expected_pct double precision NULL,
            ks2_maths_expected_pct double precision NULL,
            ks2_combined_expected_pct double precision NULL,
            ks2_reading_higher_pct double precision NULL,
            ks2_writing_higher_pct double precision NULL,
            ks2_maths_higher_pct double precision NULL,
            ks2_combined_higher_pct double precision NULL,
            ks2_source_dataset_id text NULL,
            ks2_source_dataset_version text NULL,
            ks4_source_dataset_id text NULL,
            ks4_source_dataset_version text NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_school_performance_yearly_urn "
        "ON school_performance_yearly (urn)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_school_performance_yearly_academic_year "
        "ON school_performance_yearly (academic_year)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_performance_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_performance_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_performance_yearly")
