"""persist reproducible backtest experiments

Revision ID: 0025
Revises: 0024
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0025"
down_revision: Union[str, Sequence[str], None] = "0024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "backtest_experiments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sleeve", sa.String(length=64), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("data_hash", sa.String(length=64), nullable=False),
        sa.Column("config_hash", sa.String(length=64), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("result_hash", sa.String(length=64), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "data_hash",
            "config_hash",
            "code_hash",
            name="uq_backtest_experiment_fingerprint",
        ),
    )
    op.create_index(
        "ix_backtest_experiments_created_at",
        "backtest_experiments",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_backtest_experiments_created_at",
        table_name="backtest_experiments",
    )
    op.drop_table("backtest_experiments")
