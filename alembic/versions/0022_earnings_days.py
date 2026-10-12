"""earnings_days

Revision ID: 0022
Revises: 0021
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: Union[str, Sequence[str], None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "earnings_days",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "day", name="uq_earnings_days_ticker_day"),
    )
    earnings = sa.table(
        "earnings_days",
        sa.column("id", sa.Uuid()),
        sa.column("ticker", sa.String()),
        sa.column("day", sa.Date()),
    )
    op.bulk_insert(
        earnings,
        [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "ticker": "SBER",
                "day": "2026-11-12",
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "ticker": "GAZP",
                "day": "2026-11-19",
            },
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "ticker": "LKOH",
                "day": "2026-11-26",
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("earnings_days")
