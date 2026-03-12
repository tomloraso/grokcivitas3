"""phase 19 similar school benchmarking

Revision ID: 2026031240
Revises: 2026031139
Create Date: 2026-03-12 09:00:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031240"
down_revision: str | None = "2026031139"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS metric_benchmark_cohorts_yearly (
            cohort_id uuid PRIMARY KEY,
            academic_year text NOT NULL,
            metric_key text NOT NULL,
            benchmark_scope text NOT NULL,
            cohort_type text NOT NULL,
            cohort_label text NOT NULL,
            cohort_signature text NOT NULL,
            definition_json jsonb NOT NULL,
            school_count integer NOT NULL,
            computed_at_utc timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_metric_benchmark_cohorts_yearly_signature
        ON metric_benchmark_cohorts_yearly (
            academic_year,
            metric_key,
            benchmark_scope,
            cohort_signature
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_metric_benchmark_cohorts_yearly_metric_scope
        ON metric_benchmark_cohorts_yearly (metric_key, academic_year, benchmark_scope)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS metric_benchmark_distributions_yearly (
            cohort_id uuid PRIMARY KEY REFERENCES metric_benchmark_cohorts_yearly(cohort_id)
                ON DELETE CASCADE,
            mean_value numeric(14,4) NULL,
            p10_value numeric(14,4) NULL,
            p25_value numeric(14,4) NULL,
            median_value numeric(14,4) NULL,
            p75_value numeric(14,4) NULL,
            p90_value numeric(14,4) NULL,
            minimum_value numeric(14,4) NULL,
            maximum_value numeric(14,4) NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_metric_percentiles_yearly (
            urn text NOT NULL,
            academic_year text NOT NULL,
            metric_key text NOT NULL,
            benchmark_scope text NOT NULL,
            cohort_id uuid NOT NULL REFERENCES metric_benchmark_cohorts_yearly(cohort_id)
                ON DELETE CASCADE,
            metric_value numeric(14,4) NOT NULL,
            percentile_rank numeric(7,4) NOT NULL,
            computed_at_utc timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year, metric_key, benchmark_scope)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_metric_percentiles_yearly_lookup
        ON school_metric_percentiles_yearly (urn, metric_key, academic_year)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_metric_percentiles_yearly_lookup")
    op.execute("DROP TABLE IF EXISTS school_metric_percentiles_yearly")
    op.execute("DROP TABLE IF EXISTS metric_benchmark_distributions_yearly")
    op.execute("DROP INDEX IF EXISTS ix_metric_benchmark_cohorts_yearly_metric_scope")
    op.execute("DROP INDEX IF EXISTS ux_metric_benchmark_cohorts_yearly_signature")
    op.execute("DROP TABLE IF EXISTS metric_benchmark_cohorts_yearly")
