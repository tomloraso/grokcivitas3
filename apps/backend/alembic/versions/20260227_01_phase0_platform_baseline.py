"""phase0 platform baseline

Revision ID: 2026022701
Revises:
Create Date: 2026-02-27 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026022701"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE SCHEMA IF NOT EXISTS staging")

    op.create_table(
        "pipeline_runs",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bronze_path", sa.Text(), nullable=False),
        sa.Column("downloaded_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("staged_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("promoted_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("rejected_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_pipeline_runs_source_started_at",
        "pipeline_runs",
        ["source", "started_at"],
        unique=False,
    )

    op.create_table(
        "pipeline_rejections",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pipeline_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("reason_code", sa.String(length=128), nullable=False),
        sa.Column("raw_record", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_index(
        "ix_pipeline_rejections_run_id",
        "pipeline_rejections",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_pipeline_rejections_run_id", table_name="pipeline_rejections")
    op.drop_table("pipeline_rejections")
    op.drop_index("ix_pipeline_runs_source_started_at", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")
    op.execute("DROP SCHEMA IF EXISTS staging CASCADE")
