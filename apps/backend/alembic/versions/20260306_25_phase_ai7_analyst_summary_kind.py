"""phase ai7 analyst summary kind

Revision ID: 2026030625
Revises: 2026030624
Create Date: 2026-03-06 17:20:00
"""

from collections.abc import Sequence

from sqlalchemy import inspect
from sqlalchemy.engine import Connection

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030625"
down_revision: str | None = "2026030624"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    table_names = set(inspect(connection).get_table_names())

    if "school_ai_summaries" in table_names:
        _ensure_summary_kind_column(connection, "school_ai_summaries")
        _ensure_primary_key_columns(connection, "school_ai_summaries", ["urn", "summary_kind"])

    if "school_ai_summary_history" in table_names:
        _ensure_summary_kind_column(connection, "school_ai_summary_history")

    if "ai_generation_runs" in table_names:
        _ensure_summary_kind_column(connection, "ai_generation_runs")


def downgrade() -> None:
    connection = op.get_bind()
    table_names = set(inspect(connection).get_table_names())

    if "school_ai_summary_history" in table_names:
        op.execute("DELETE FROM school_ai_summary_history WHERE summary_kind <> 'overview'")
        op.execute("ALTER TABLE school_ai_summary_history DROP COLUMN IF EXISTS summary_kind")

    if "school_ai_summaries" in table_names:
        op.execute("DELETE FROM school_ai_summaries WHERE summary_kind <> 'overview'")
        _ensure_primary_key_columns(connection, "school_ai_summaries", ["urn"])
        op.execute("ALTER TABLE school_ai_summaries DROP COLUMN IF EXISTS summary_kind")
        _ensure_primary_key_columns(connection, "school_ai_summaries", ["urn"])

    if "ai_generation_runs" in table_names:
        op.execute("DELETE FROM ai_generation_runs WHERE summary_kind <> 'overview'")
        op.execute("ALTER TABLE ai_generation_runs DROP COLUMN IF EXISTS summary_kind")


def _ensure_summary_kind_column(connection: Connection, table_name: str) -> None:
    columns = _column_names(connection, table_name)
    if "summary_kind" not in columns:
        op.execute(f"ALTER TABLE {table_name} ADD COLUMN summary_kind text NULL")

    op.execute(f"UPDATE {table_name} SET summary_kind = 'overview' WHERE summary_kind IS NULL")
    op.execute(f"ALTER TABLE {table_name} ALTER COLUMN summary_kind SET NOT NULL")


def _column_names(connection: Connection, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(connection).get_columns(table_name)}


def _ensure_primary_key_columns(
    connection: Connection,
    table_name: str,
    columns: list[str],
) -> None:
    primary_key = inspect(connection).get_pk_constraint(table_name)
    current_columns = list(primary_key.get("constrained_columns") or [])
    if current_columns == columns:
        return

    constraint_name = primary_key.get("name")
    if isinstance(constraint_name, str) and constraint_name:
        op.execute(f'ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS "{constraint_name}"')

    joined_columns = ", ".join(columns)
    op.execute(f"ALTER TABLE {table_name} ADD PRIMARY KEY ({joined_columns})")
