"""news_events

Revision ID: 0020
Revises: 0019
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

revision: str = "0020"
down_revision: Union[str, Sequence[str], None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "news_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=256), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("tickers", ARRAY(sa.String(length=32)), nullable=False),
        sa.Column(
            "raw",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_news_events_url"),
        sa.UniqueConstraint("source", "source_id", name="uq_news_events_source_id"),
    )
    op.create_index("ix_news_events_ts", "news_events", ["ts"])


def downgrade() -> None:
    op.drop_index("ix_news_events_ts", table_name="news_events")
    op.drop_table("news_events")
