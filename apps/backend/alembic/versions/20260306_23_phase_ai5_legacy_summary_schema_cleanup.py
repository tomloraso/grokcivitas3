"""phase ai5 legacy summary schema cleanup

Revision ID: 2026030623
Revises: 2026030522
Create Date: 2026-03-06 12:20:00
"""

from collections.abc import Sequence

from sqlalchemy import inspect
from sqlalchemy.engine import Connection

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030623"
down_revision: str | None = "2026030522"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    table_names = set(inspect(connection).get_table_names())

    if "ai_generation_run_items" in table_names and "ai_generation_runs" in table_names:
        _cleanup_legacy_run_items(connection)
        _cleanup_legacy_runs(connection)

    if "school_ai_summaries" in table_names:
        _cleanup_legacy_current_summaries(connection)

    if "school_ai_summary_history" in table_names:
        _cleanup_legacy_summary_history(connection)


def downgrade() -> None:
    # This migration deletes legacy non-overview records and drops obsolete columns.
    # The old multi-summary schema cannot be reconstructed automatically.
    return None


def _cleanup_legacy_current_summaries(connection: Connection) -> None:
    columns = _column_names(connection, "school_ai_summaries")
    if "summary_type" not in columns:
        return

    op.execute("DELETE FROM school_ai_summaries WHERE summary_type <> 'overview'")
    _ensure_primary_key_columns(connection, "school_ai_summaries", ["urn"])
    op.execute("ALTER TABLE school_ai_summaries DROP COLUMN IF EXISTS summary_type")
    _ensure_primary_key_columns(connection, "school_ai_summaries", ["urn"])


def _cleanup_legacy_summary_history(connection: Connection) -> None:
    columns = _column_names(connection, "school_ai_summary_history")
    if "summary_type" not in columns:
        return

    op.execute("DELETE FROM school_ai_summary_history WHERE summary_type <> 'overview'")
    op.execute("ALTER TABLE school_ai_summary_history DROP COLUMN IF EXISTS summary_type")


def _cleanup_legacy_run_items(connection: Connection) -> None:
    columns = _column_names(connection, "ai_generation_run_items")
    if "summary_type" in columns:
        op.execute(
            """
            DELETE FROM ai_generation_run_items
            WHERE summary_type <> 'overview'
               OR run_id IN (
                    SELECT id
                    FROM ai_generation_runs
                    WHERE summary_type <> 'overview'
               )
            """
        )
        _ensure_primary_key_columns(connection, "ai_generation_run_items", ["run_id", "urn"])
        op.execute("ALTER TABLE ai_generation_run_items DROP COLUMN IF EXISTS summary_type")

    for column in ("data_version_hash", "provider_batch_request_id"):
        op.execute(f"ALTER TABLE ai_generation_run_items DROP COLUMN IF EXISTS {column}")

    _ensure_primary_key_columns(connection, "ai_generation_run_items", ["run_id", "urn"])


def _cleanup_legacy_runs(connection: Connection) -> None:
    columns = _column_names(connection, "ai_generation_runs")
    if "summary_type" in columns:
        op.execute("DELETE FROM ai_generation_runs WHERE summary_type <> 'overview'")
        op.execute("ALTER TABLE ai_generation_runs DROP COLUMN IF EXISTS summary_type")

    for column in (
        "provider_batch_id",
        "provider_batch_status",
        "provider_batch_requested_count",
        "provider_batch_submitted_at",
        "provider_batch_completed_at",
        "provider_batch_last_polled_at",
        "provider_batch_error_message",
    ):
        op.execute(f"ALTER TABLE ai_generation_runs DROP COLUMN IF EXISTS {column}")


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
