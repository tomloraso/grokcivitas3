"""phase hardening data quality snapshots and pipeline run events

Revision ID: 2026030310
Revises: 2026030309
Create Date: 2026-03-03 20:30:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030310"
down_revision: str | None = "2026030309"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS data_quality_snapshots (
            snapshot_date date NOT NULL,
            source text NOT NULL,
            dataset text NOT NULL,
            section text NOT NULL,
            source_updated_at timestamptz NULL,
            section_updated_at timestamptz NULL,
            source_freshness_lag_hours double precision NULL,
            section_freshness_lag_hours double precision NULL,
            schools_total_count integer NOT NULL,
            schools_with_section_count integer NOT NULL,
            section_coverage_ratio double precision NOT NULL,
            trends_zero_years_count integer NOT NULL DEFAULT 0,
            trends_one_year_count integer NOT NULL DEFAULT 0,
            trends_two_plus_years_count integer NOT NULL DEFAULT 0,
            contract_version text NULL,
            created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (snapshot_date, source, dataset, section),
            CHECK (section_coverage_ratio >= 0.0 AND section_coverage_ratio <= 1.0)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_data_quality_snapshots_source_section_snapshot_date
        ON data_quality_snapshots (source, section, snapshot_date DESC)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_run_events (
            id bigserial PRIMARY KEY,
            run_id uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
            source text NOT NULL,
            dataset text NOT NULL,
            section text NULL,
            academic_year text NULL,
            run_status text NOT NULL,
            contract_version text NULL,
            started_at timestamptz NOT NULL,
            finished_at timestamptz NOT NULL,
            duration_seconds double precision NOT NULL,
            downloaded_rows integer NOT NULL DEFAULT 0,
            staged_rows integer NOT NULL DEFAULT 0,
            promoted_rows integer NOT NULL DEFAULT 0,
            rejected_rows integer NOT NULL DEFAULT 0,
            rejected_ratio double precision NULL,
            error_message text NULL,
            created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            UNIQUE (run_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_pipeline_run_events_source_finished_at
        ON pipeline_run_events (source, finished_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_pipeline_run_events_run_status
        ON pipeline_run_events (run_status)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_pipeline_run_events_run_status")
    op.execute("DROP INDEX IF EXISTS ix_pipeline_run_events_source_finished_at")
    op.execute("DROP TABLE IF EXISTS pipeline_run_events")
    op.execute("DROP INDEX IF EXISTS ix_data_quality_snapshots_source_section_snapshot_date")
    op.execute("DROP TABLE IF EXISTS data_quality_snapshots")
