"""phase 17 school admissions yearly

Revision ID: 2026031037
Revises: 2026031036
Create Date: 2026-03-10 18:10:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031037"
down_revision: str | None = "2026031036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_admissions_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            entry_year text NULL,
            school_laestab text NULL,
            school_phase text NULL,
            school_name text NOT NULL,
            places_offered_total integer NULL,
            preferred_offers_total integer NULL,
            first_preference_offers integer NULL,
            second_preference_offers integer NULL,
            third_preference_offers integer NULL,
            applications_any_preference integer NULL,
            applications_first_preference integer NULL,
            applications_second_preference integer NULL,
            applications_third_preference integer NULL,
            first_preference_application_to_offer_ratio double precision NULL,
            first_preference_application_to_total_places_ratio double precision NULL,
            cross_la_applications integer NULL,
            cross_la_offers integer NULL,
            admissions_policy text NULL,
            establishment_type text NULL,
            denomination text NULL,
            fsm_eligible_pct double precision NULL,
            urban_rural text NULL,
            allthrough_school boolean NULL,
            oversubscription_ratio double precision NULL,
            first_preference_offer_rate double precision NULL,
            any_preference_offer_rate double precision NULL,
            source_file_url text NOT NULL,
            source_updated_at_utc timestamptz NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_admissions_yearly_urn
        ON school_admissions_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_admissions_yearly_academic_year
        ON school_admissions_yearly (academic_year)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_admissions_yearly_school_laestab
        ON school_admissions_yearly (school_laestab)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_admissions_yearly_school_laestab")
    op.execute("DROP INDEX IF EXISTS ix_school_admissions_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_admissions_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_admissions_yearly")
