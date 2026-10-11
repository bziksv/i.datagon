"""indexes

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, Sequence[str], None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_candles_ts", "candles", ["ts"])
    op.create_index("ix_orders_status_created_at", "orders", ["status", "created_at"])
    op.create_index("ix_ledger_entries_ts", "ledger_entries", ["ts"])


def downgrade() -> None:
    op.drop_index("ix_ledger_entries_ts", table_name="ledger_entries")
    op.drop_index("ix_orders_status_created_at", table_name="orders")
    op.drop_index("ix_candles_ts", table_name="candles")
    op.drop_column("orders", "created_at")
