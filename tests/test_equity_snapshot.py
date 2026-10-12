from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models import EquitySnapshot
from worker.equity import record_snapshot, snapshot_due, take_snapshot


def test_worker_tick_writes_snapshot_row() -> None:
    now = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
    assert snapshot_due(None, now) is True
    row = take_snapshot(
        trading_cash=Decimal("999000"),
        vault=Decimal("0"),
        positions_value=Decimal("1000"),
        ts=now,
    )
    assert isinstance(row, EquitySnapshot)
    assert row.ts == now
    assert Decimal(str(row.trading_cash)) == Decimal("999000")
    assert Decimal(str(row.positions_value)) == Decimal("1000")
    assert Decimal(str(row.equity)) == Decimal("1000000")

    table: list[EquitySnapshot] = []
    record_snapshot(table, row)
    assert len(table) == 1
    assert table[0] is row

    later = now + timedelta(hours=1)
    assert snapshot_due(now, later) is True
    assert snapshot_due(now, now + timedelta(minutes=10)) is False
