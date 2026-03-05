"""phase m5 area context and house prices

Revision ID: 2026030518
Revises: 2026030517
Create Date: 2026-03-05 19:05:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030518"
down_revision: str | None = "2026030517"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS income_score double precision NULL"
    )
    op.execute("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS income_rank integer NULL")
    op.execute("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS income_decile integer NULL")
    op.execute(
        "ALTER TABLE area_deprivation "
        "ADD COLUMN IF NOT EXISTS employment_score double precision NULL"
    )
    op.execute("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS employment_rank integer NULL")
    op.execute(
        "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS employment_decile integer NULL"
    )
    op.execute(
        "ALTER TABLE area_deprivation "
        "ADD COLUMN IF NOT EXISTS education_score double precision NULL"
    )
    op.execute("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS education_rank integer NULL")
    op.execute(
        "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS education_decile integer NULL"
    )
    op.execute(
        "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS health_score double precision NULL"
    )
    op.execute("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS health_rank integer NULL")
    op.execute("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS health_decile integer NULL")
    op.execute(
        "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS crime_score double precision NULL"
    )
    op.execute("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS crime_rank integer NULL")
    op.execute("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS crime_decile integer NULL")
    op.execute(
        "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS barriers_score double precision NULL"
    )
    op.execute("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS barriers_rank integer NULL")
    op.execute("ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS barriers_decile integer NULL")
    op.execute(
        "ALTER TABLE area_deprivation "
        "ADD COLUMN IF NOT EXISTS living_environment_score double precision NULL"
    )
    op.execute(
        "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS living_environment_rank integer NULL"
    )
    op.execute(
        "ALTER TABLE area_deprivation "
        "ADD COLUMN IF NOT EXISTS living_environment_decile integer NULL"
    )
    op.execute(
        "ALTER TABLE area_deprivation ADD COLUMN IF NOT EXISTS population_total integer NULL"
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_area_deprivation_lad_code
        ON area_deprivation (local_authority_district_code)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS area_house_price_context (
            area_code text NOT NULL,
            area_name text NOT NULL,
            month date NOT NULL,
            average_price double precision NOT NULL,
            monthly_change_pct double precision NULL,
            annual_change_pct double precision NULL,
            source_dataset_id text NOT NULL,
            source_dataset_version text NULL,
            source_file_url text NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (area_code, month)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_area_house_price_context_month
        ON area_house_price_context (month)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_area_house_price_context_area_code
        ON area_house_price_context (area_code)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_area_house_price_context_area_code")
    op.execute("DROP INDEX IF EXISTS ix_area_house_price_context_month")
    op.execute("DROP TABLE IF EXISTS area_house_price_context")

    op.execute("DROP INDEX IF EXISTS ix_area_deprivation_lad_code")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS population_total")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS living_environment_decile")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS living_environment_rank")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS living_environment_score")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS barriers_decile")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS barriers_rank")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS barriers_score")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS crime_decile")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS crime_rank")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS crime_score")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS health_decile")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS health_rank")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS health_score")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS education_decile")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS education_rank")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS education_score")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS employment_decile")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS employment_rank")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS employment_score")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS income_decile")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS income_rank")
    op.execute("ALTER TABLE area_deprivation DROP COLUMN IF EXISTS income_score")
