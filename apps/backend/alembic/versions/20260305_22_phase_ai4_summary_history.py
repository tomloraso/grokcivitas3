"""phase ai4 summary history

Revision ID: 2026030522
Revises: 2026030521
Create Date: 2026-03-05 23:58:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030522"
down_revision: str | None = "2026030521"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_ai_summary_history (
            id uuid PRIMARY KEY,
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            text text NOT NULL,
            data_version_hash text NOT NULL,
            prompt_version text NOT NULL,
            model_id text NOT NULL,
            generated_at timestamptz NOT NULL,
            superseded_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_ai_summary_history_urn
        ON school_ai_summary_history (urn)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_ai_summary_history_urn")
    op.execute("DROP TABLE IF EXISTS school_ai_summary_history")
