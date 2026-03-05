"""phase m1 ofsted latest sub-judgements and dates

Revision ID: 2026030414
Revises: 2026030413
Create Date: 2026-03-04 18:30:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026030414"
down_revision: str | None = "2026030413"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS latest_oeif_inspection_start_date date NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS latest_oeif_publication_date date NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS quality_of_education_code text NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS quality_of_education_label text NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS behaviour_and_attitudes_code text NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS behaviour_and_attitudes_label text NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS personal_development_code text NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS personal_development_label text NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS leadership_and_management_code text NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS leadership_and_management_label text NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS latest_ungraded_inspection_date date NULL"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest "
        "ADD COLUMN IF NOT EXISTS latest_ungraded_publication_date date NULL"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS latest_ungraded_publication_date"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS latest_ungraded_inspection_date"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS leadership_and_management_label"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS leadership_and_management_code"
    )
    op.execute("ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS personal_development_label")
    op.execute("ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS personal_development_code")
    op.execute(
        "ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS behaviour_and_attitudes_label"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS behaviour_and_attitudes_code"
    )
    op.execute("ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS quality_of_education_label")
    op.execute("ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS quality_of_education_code")
    op.execute(
        "ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS latest_oeif_publication_date"
    )
    op.execute(
        "ALTER TABLE school_ofsted_latest DROP COLUMN IF EXISTS latest_oeif_inspection_start_date"
    )
