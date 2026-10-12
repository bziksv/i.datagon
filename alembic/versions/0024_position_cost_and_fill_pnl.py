"""position cost including buy fees and realized fill PnL

Revision ID: 0024
Revises: 0023
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: Union[str, Sequence[str], None] = "0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "positions",
        sa.Column("avg_cost", sa.Numeric(18, 6), nullable=True),
    )
    op.execute("UPDATE positions SET avg_cost = avg_price WHERE avg_cost IS NULL")
    op.add_column(
        "fills",
        sa.Column("realized_gross_pnl", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "fills",
        sa.Column("realized_net_pnl", sa.Numeric(18, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("fills", "realized_net_pnl")
    op.drop_column("fills", "realized_gross_pnl")
    op.drop_column("positions", "avg_cost")
