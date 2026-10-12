"""Снимок equity для таблицы equity_snapshots."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.book.commission import compute_equity
from app.models import EquitySnapshot


def make_snapshot(
    *,
    trading_cash: Decimal,
    vault: Decimal = Decimal("0"),
    positions_value: Decimal = Decimal("0"),
    ts: datetime | None = None,
) -> EquitySnapshot:
    equity = compute_equity(trading_cash, vault, positions_value)
    return EquitySnapshot(
        id=uuid4(),
        ts=ts or datetime.now(UTC),
        trading_cash=trading_cash,
        vault=vault,
        positions_value=positions_value,
        equity=equity,
    )
