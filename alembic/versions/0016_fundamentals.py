"""fundamentals

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0016"
down_revision: Union[str, Sequence[str], None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fundamentals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("asset_uid", sa.String(length=64), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pe_ratio_ttm", sa.Numeric(18, 6), nullable=True),
        sa.Column("price_to_book_ttm", sa.Numeric(18, 6), nullable=True),
        sa.Column("eps_ttm", sa.Numeric(18, 6), nullable=True),
        sa.Column("market_capitalization", sa.Numeric(20, 4), nullable=True),
        sa.Column(
            "raw",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", name="uq_fundamentals_ticker"),
    )


def downgrade() -> None:
    op.drop_table("fundamentals")
