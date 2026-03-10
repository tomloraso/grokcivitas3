"""phase 15 school financials yearly

Revision ID: 2026031033
Revises: 2026031032
Create Date: 2026-03-10 13:30:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031033"
down_revision: str | None = "2026031032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS school_financials_yearly (
            urn text NOT NULL REFERENCES schools(urn) ON DELETE CASCADE,
            academic_year text NOT NULL,
            finance_source text NOT NULL DEFAULT 'aar',
            school_laestab text NULL,
            school_name text NOT NULL,
            trust_uid text NULL,
            trust_name text NULL,
            phase text NULL,
            overall_phase text NULL,
            admissions_policy text NULL,
            urban_rural text NULL,
            pupils_fte double precision NULL,
            teachers_fte double precision NULL,
            fsm_pct double precision NULL,
            ehcp_pct double precision NULL,
            sen_support_pct double precision NULL,
            eal_pct double precision NULL,
            total_grant_funding_gbp double precision NULL,
            total_self_generated_funding_gbp double precision NULL,
            total_income_gbp double precision NULL,
            teaching_staff_costs_gbp double precision NULL,
            supply_teaching_staff_costs_gbp double precision NULL,
            education_support_staff_costs_gbp double precision NULL,
            other_staff_costs_gbp double precision NULL,
            total_staff_costs_gbp double precision NULL,
            maintenance_improvement_costs_gbp double precision NULL,
            premises_costs_gbp double precision NULL,
            educational_supplies_costs_gbp double precision NULL,
            bought_in_professional_services_costs_gbp double precision NULL,
            catering_costs_gbp double precision NULL,
            total_expenditure_gbp double precision NULL,
            revenue_reserve_gbp double precision NULL,
            in_year_balance_gbp double precision NULL,
            income_per_pupil_gbp double precision NULL,
            expenditure_per_pupil_gbp double precision NULL,
            staff_costs_pct_of_expenditure double precision NULL,
            teaching_staff_costs_per_pupil_gbp double precision NULL,
            supply_staff_costs_pct_of_staff_costs double precision NULL,
            revenue_reserve_per_pupil_gbp double precision NULL,
            source_file_url text NOT NULL,
            source_updated_at_utc timestamptz NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
            PRIMARY KEY (urn, academic_year)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_financials_yearly_urn
        ON school_financials_yearly (urn)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_school_financials_yearly_academic_year
        ON school_financials_yearly (academic_year)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_school_financials_yearly_academic_year")
    op.execute("DROP INDEX IF EXISTS ix_school_financials_yearly_urn")
    op.execute("DROP TABLE IF EXISTS school_financials_yearly")
