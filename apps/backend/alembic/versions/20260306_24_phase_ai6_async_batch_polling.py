"""phase ai6 async batch polling

Revision ID: 2026030624
Revises: 2026030623
Create Date: 2026-03-06 15:10:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030624"
down_revision: str | None = "2026030623"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE ai_generation_run_items
        ADD COLUMN IF NOT EXISTS data_version_hash text NULL
        """
    )
    op.execute(
        """
        ALTER TABLE ai_generation_run_items
        ADD COLUMN IF NOT EXISTS provider_name text NULL
        """
    )
    op.execute(
        """
        ALTER TABLE ai_generation_run_items
        ADD COLUMN IF NOT EXISTS provider_batch_id text NULL
        """
    )
    op.execute(
        """
        ALTER TABLE ai_generation_run_items
        ADD COLUMN IF NOT EXISTS prompt_version text NULL
        """
    )
    op.execute(
        """
        ALTER TABLE ai_generation_run_items
        ADD COLUMN IF NOT EXISTS submitted_at timestamptz NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ai_generation_run_items_pending_batch
        ON ai_generation_run_items (status, provider_name, provider_batch_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_ai_generation_run_items_pending_batch")
    op.execute("ALTER TABLE ai_generation_run_items DROP COLUMN IF EXISTS submitted_at")
    op.execute("ALTER TABLE ai_generation_run_items DROP COLUMN IF EXISTS prompt_version")
    op.execute("ALTER TABLE ai_generation_run_items DROP COLUMN IF EXISTS provider_batch_id")
    op.execute("ALTER TABLE ai_generation_run_items DROP COLUMN IF EXISTS provider_name")
    op.execute("ALTER TABLE ai_generation_run_items DROP COLUMN IF EXISTS data_version_hash")
