"""phase hardening pipeline checkpoints and source locks

Revision ID: 2026030311
Revises: 2026030310
Create Date: 2026-03-03 22:30:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030311"
down_revision: str | None = "2026030310"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_checkpoints (
            run_id uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
            source text NOT NULL,
            step text NOT NULL,
            status text NOT NULL,
            attempts integer NOT NULL DEFAULT 0,
            retryable boolean NOT NULL DEFAULT false,
            payload jsonb NOT NULL DEFAULT '{}'::jsonb,
            error_message text NULL,
            created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (run_id, source, step)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_pipeline_checkpoints_source_updated_at
        ON pipeline_checkpoints (source, updated_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_pipeline_checkpoints_status
        ON pipeline_checkpoints (status)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_source_locks (
            source text PRIMARY KEY,
            run_id uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
            acquired_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_pipeline_source_locks_acquired_at
        ON pipeline_source_locks (acquired_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_pipeline_source_locks_acquired_at")
    op.execute("DROP TABLE IF EXISTS pipeline_source_locks")
    op.execute("DROP INDEX IF EXISTS ix_pipeline_checkpoints_status")
    op.execute("DROP INDEX IF EXISTS ix_pipeline_checkpoints_source_updated_at")
    op.execute("DROP TABLE IF EXISTS pipeline_checkpoints")
