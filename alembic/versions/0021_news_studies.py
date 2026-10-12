"""news_studies

Revision ID: 0021
Revises: 0020
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0021"
down_revision: Union[str, Sequence[str], None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "news_studies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("news_event_id", sa.Uuid(), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("horizon_n", sa.Integer(), nullable=False),
        sa.Column("t_minus_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("t_plus_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ret", sa.Numeric(18, 8), nullable=False),
        sa.Column(
            "payload",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(["news_event_id"], ["news_events.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "news_event_id",
            "ticker",
            "horizon_n",
            name="uq_news_studies_event_ticker_n",
        ),
    )


def downgrade() -> None:
    op.drop_table("news_studies")
