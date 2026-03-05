"""phase m6 metric benchmarks

Revision ID: 2026030519
Revises: 2026030518
Create Date: 2026-03-05 22:25:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030519"
down_revision: str | None = "2026030518"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS metric_benchmarks_yearly (
            metric_key text NOT NULL,
            academic_year text NOT NULL,
            benchmark_scope text NOT NULL,
            benchmark_area text NOT NULL,
            benchmark_label text NOT NULL,
            benchmark_value double precision NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (metric_key, academic_year, benchmark_scope, benchmark_area)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_metric_benchmarks_yearly_metric_year
        ON metric_benchmarks_yearly (metric_key, academic_year)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_metric_benchmarks_yearly_scope_area
        ON metric_benchmarks_yearly (benchmark_scope, benchmark_area)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_metric_benchmarks_yearly_scope_area")
    op.execute("DROP INDEX IF EXISTS ix_metric_benchmarks_yearly_metric_year")
    op.execute("DROP TABLE IF EXISTS metric_benchmarks_yearly")
