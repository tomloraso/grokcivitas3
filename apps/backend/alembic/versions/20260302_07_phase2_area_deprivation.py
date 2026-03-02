"""phase2 area deprivation table

Revision ID: 2026030207
Revises: 2026030206
Create Date: 2026-03-02 21:15:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030207"
down_revision: str | None = "2026030206"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE area_deprivation (
            lsoa_code text PRIMARY KEY,
            lsoa_name text NOT NULL,
            local_authority_district_code text NULL,
            local_authority_district_name text NULL,
            imd_score double precision NOT NULL,
            imd_rank integer NOT NULL,
            imd_decile integer NOT NULL,
            idaci_score double precision NOT NULL,
            idaci_rank integer NOT NULL,
            idaci_decile integer NOT NULL,
            source_release text NOT NULL,
            lsoa_vintage text NOT NULL,
            source_file_url text NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute("CREATE INDEX ix_area_deprivation_imd_decile ON area_deprivation (imd_decile)")
    op.execute("CREATE INDEX ix_area_deprivation_idaci_decile ON area_deprivation (idaci_decile)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_area_deprivation_idaci_decile")
    op.execute("DROP INDEX IF EXISTS ix_area_deprivation_imd_decile")
    op.execute("DROP TABLE IF EXISTS area_deprivation")
