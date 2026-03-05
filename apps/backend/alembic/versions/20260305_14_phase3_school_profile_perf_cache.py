"""phase3 school profile performance and cache metadata

Revision ID: 2026030514
Revises: 2026030414
Create Date: 2026-03-05 00:20:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030514"
down_revision: str | None = "2026030414"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_cache_versions (
            cache_key text PRIMARY KEY,
            version_updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute(
        """
        INSERT INTO app_cache_versions (cache_key, version_updated_at)
        VALUES ('school_profile', timezone('utc', now()))
        ON CONFLICT (cache_key) DO NOTHING
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS area_crime_global_metadata (
            id smallint PRIMARY KEY CHECK (id = 1),
            months_available integer NOT NULL,
            latest_updated_at timestamptz NULL,
            latest_month date NULL,
            latest_radius_meters double precision NULL,
            refreshed_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute(
        """
        INSERT INTO area_crime_global_metadata (
            id,
            months_available,
            latest_updated_at,
            latest_month,
            latest_radius_meters,
            refreshed_at
        )
        SELECT
            1,
            COALESCE((SELECT COUNT(DISTINCT month) FROM area_crime_context), 0)::integer,
            (SELECT MAX(updated_at) FROM area_crime_context),
            (SELECT MAX(month) FROM area_crime_context),
            (
                SELECT radius_meters
                FROM area_crime_context
                ORDER BY month DESC, updated_at DESC, radius_meters DESC
                LIMIT 1
            ),
            timezone('utc', now())
        ON CONFLICT (id) DO UPDATE SET
            months_available = EXCLUDED.months_available,
            latest_updated_at = EXCLUDED.latest_updated_at,
            latest_month = EXCLUDED.latest_month,
            latest_radius_meters = EXCLUDED.latest_radius_meters,
            refreshed_at = timezone('utc', now())
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_area_crime_context_urn_month_radius_desc
        ON area_crime_context (urn, month DESC, radius_meters DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_area_crime_context_urn_updated_at_desc
        ON area_crime_context (urn, updated_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_area_crime_context_month_updated_radius_desc
        ON area_crime_context (month DESC, updated_at DESC, radius_meters DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_area_crime_context_updated_at_desc
        ON area_crime_context (updated_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_area_crime_context_updated_at_desc")
    op.execute("DROP INDEX IF EXISTS ix_area_crime_context_month_updated_radius_desc")
    op.execute("DROP INDEX IF EXISTS ix_area_crime_context_urn_updated_at_desc")
    op.execute("DROP INDEX IF EXISTS ix_area_crime_context_urn_month_radius_desc")
    op.execute("DROP TABLE IF EXISTS area_crime_global_metadata")
    op.execute("DROP TABLE IF EXISTS app_cache_versions")
