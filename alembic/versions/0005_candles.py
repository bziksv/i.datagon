"""candles

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("tf", sa.String(length=8), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("o", sa.Numeric(18, 6), nullable=False),
        sa.Column("h", sa.Numeric(18, 6), nullable=False),
        sa.Column("l", sa.Numeric(18, 6), nullable=False),
        sa.Column("c", sa.Numeric(18, 6), nullable=False),
        sa.Column("v", sa.Numeric(20, 4), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instrument_id", "tf", "ts", name="uq_candles_instrument_tf_ts"
        ),
    )


def downgrade() -> None:
    op.drop_table("candles")
