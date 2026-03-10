"""merge payment and financial benchmark heads

Revision ID: 2026031034
Revises: 2026030930, 2026031033
Create Date: 2026-03-10 16:20:00
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "2026031034"
down_revision: tuple[str, str] = ("2026030930", "2026031033")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
