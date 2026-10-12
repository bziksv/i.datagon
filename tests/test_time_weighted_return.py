from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.book.accounts import TRADING_CASH
from app.book.returns import time_weighted_return
from app.models import EquitySnapshot, LedgerEntry


def _snapshot(ts: datetime, equity: str) -> EquitySnapshot:
    value = Decimal(equity)
    return EquitySnapshot(
        id=uuid4(),
        ts=ts,
        trading_cash=value,
        vault=Decimal("0"),
        positions_value=Decimal("0"),
        equity=value,
    )


def test_deposit_is_not_counted_as_profit() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    snapshots = [
        _snapshot(start, "1000"),
        _snapshot(start + timedelta(days=1), "2100"),
        _snapshot(start + timedelta(days=2), "2310"),
    ]
    deposit = LedgerEntry(
        account_kind=TRADING_CASH,
        amount=Decimal("1000"),
        reason="deposit",
        ts=start + timedelta(hours=12),
    )
    result = time_weighted_return(snapshots, [deposit])
    # First period: (2100 - 1000) / 1000 - 1 = 10%.
    # Second period: 2310 / 2100 - 1 = 10%; compounded = 21%.
    assert result == Decimal("0.21")


def test_twr_requires_two_valuations() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    assert time_weighted_return([_snapshot(start, "1000")]) is None
