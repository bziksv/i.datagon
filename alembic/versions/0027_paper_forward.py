"""paper-forward qualification campaigns

Revision ID: 0027
Revises: 0026
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: Union[str, Sequence[str], None] = "0026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "paper_forward_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sleeve", sa.String(length=64), nullable=False),
        sa.Column("experiment_id", sa.UUID(), nullable=False),
        sa.Column("minimum_days", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["backtest_experiments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_paper_forward_runs_started_at",
        "paper_forward_runs",
        ["started_at"],
        unique=False,
    )
    op.create_table(
        "paper_forward_observations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("strategy_equity", sa.Numeric(18, 2), nullable=False),
        sa.Column("benchmark_equity", sa.Numeric(18, 2), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["paper_forward_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id",
            "observed_at",
            name="uq_paper_forward_run_observed_at",
        ),
    )
    op.create_index(
        "ix_paper_forward_observations_run_id",
        "paper_forward_observations",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_paper_forward_observations_run_id",
        table_name="paper_forward_observations",
    )
    op.drop_table("paper_forward_observations")
    op.drop_index(
        "ix_paper_forward_runs_started_at",
        table_name="paper_forward_runs",
    )
    op.drop_table("paper_forward_runs")
