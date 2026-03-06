"""phase ai2 summary storage

Revision ID: 2026030521
Revises: 2026030520
Create Date: 2026-03-05 23:55:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030521"
down_revision: str | None = "2026030520"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_ai_summaries (
            urn text PRIMARY KEY REFERENCES schools(urn) ON DELETE CASCADE,
            text text NOT NULL,
            data_version_hash text NOT NULL,
            prompt_version text NOT NULL,
            model_id text NOT NULL,
            generated_at timestamptz NOT NULL,
            generation_duration_ms integer NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_ai_summaries_data_version_hash
        ON school_ai_summaries (data_version_hash)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_generation_runs (
            id uuid PRIMARY KEY,
            trigger text NOT NULL,
            requested_count integer NOT NULL,
            succeeded_count integer NOT NULL DEFAULT 0,
            generation_failed_count integer NOT NULL DEFAULT 0,
            validation_failed_count integer NOT NULL DEFAULT 0,
            started_at timestamptz NOT NULL,
            completed_at timestamptz NULL,
            status text NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_generation_run_items (
            run_id uuid NOT NULL REFERENCES ai_generation_runs(id) ON DELETE CASCADE,
            urn text NOT NULL,
            status text NOT NULL,
            attempt_count integer NOT NULL DEFAULT 0,
            failure_reason_codes text[] NULL,
            completed_at timestamptz NULL,
            PRIMARY KEY (run_id, urn)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ai_generation_runs_status
        ON ai_generation_runs (status)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ai_generation_run_items_run_status
        ON ai_generation_run_items (run_id, status)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_ai_generation_run_items_run_status")
    op.execute("DROP INDEX IF EXISTS ix_ai_generation_runs_status")
    op.execute("DROP TABLE IF EXISTS ai_generation_run_items")
    op.execute("DROP TABLE IF EXISTS ai_generation_runs")
    op.execute("DROP INDEX IF EXISTS ix_school_ai_summaries_data_version_hash")
    op.execute("DROP TABLE IF EXISTS school_ai_summaries")
