"""fills.execution_id for idempotent partial executions

Revision ID: 0023
Revises: 0022
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: Union[str, Sequence[str], None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "fills",
        sa.Column("execution_id", sa.String(length=128), nullable=True),
    )
    op.create_unique_constraint(
        "uq_fills_execution_id",
        "fills",
        ["execution_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_fills_execution_id", "fills", type_="unique")
    op.drop_column("fills", "execution_id")
