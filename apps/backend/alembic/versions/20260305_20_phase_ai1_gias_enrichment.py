"""phase ai1 gias enrichment

Revision ID: 2026030520
Revises: 2026030519
Create Date: 2026-03-05 23:35:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030520"
down_revision: str | None = "2026030519"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS website text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS telephone text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS head_title text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS head_first_name text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS head_last_name text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS head_job_title text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS address_street text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS address_locality text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS address_line3 text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS address_town text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS address_county text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS statutory_low_age integer NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS statutory_high_age integer NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS gender text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS religious_character text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS diocese text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS admissions_policy text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS sixth_form text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS nursery_provision text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS boarders text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS fsm_pct_gias double precision NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS trust_name text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS trust_flag text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS federation_name text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS federation_flag text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS la_name text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS la_code text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS urban_rural text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS number_of_boys integer NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS number_of_girls integer NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS lsoa_code text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS lsoa_name text NULL")
    op.execute("ALTER TABLE schools ADD COLUMN IF NOT EXISTS last_changed_date date NULL")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_normalization_warnings (
            id bigserial PRIMARY KEY,
            run_id uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
            source text NOT NULL,
            field_name text NOT NULL,
            reason_code text NOT NULL,
            warning_count integer NOT NULL,
            created_at timestamptz NOT NULL DEFAULT timezone('utc', now())
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_pipeline_normalization_warnings_run_source
        ON pipeline_normalization_warnings (run_id, source)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_pipeline_normalization_warnings_run_source")
    op.execute("DROP TABLE IF EXISTS pipeline_normalization_warnings")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS last_changed_date")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS lsoa_name")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS lsoa_code")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS number_of_girls")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS number_of_boys")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS urban_rural")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS la_code")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS la_name")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS federation_flag")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS federation_name")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS trust_flag")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS trust_name")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS fsm_pct_gias")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS boarders")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS nursery_provision")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS sixth_form")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS admissions_policy")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS diocese")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS religious_character")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS gender")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS statutory_high_age")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS statutory_low_age")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS address_county")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS address_town")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS address_line3")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS address_locality")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS address_street")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS head_job_title")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS head_last_name")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS head_first_name")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS head_title")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS telephone")
    op.execute("ALTER TABLE schools DROP COLUMN IF EXISTS website")
