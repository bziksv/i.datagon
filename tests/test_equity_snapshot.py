import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models import EquitySnapshot
from worker import equity as worker_equity
from worker.equity import (
    persist_valuation_snapshot,
    record_snapshot,
    snapshot_due,
    take_snapshot,
)


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


def test_worker_persists_snapshot_from_shared_valuation(monkeypatch) -> None:
    class Session:
        def __init__(self) -> None:
            self.added = []
            self.committed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        def add(self, row) -> None:
            self.added.append(row)

        async def commit(self) -> None:
            self.committed = True

    session = Session()

    async def valuation(_session, *, now):
        return {
            "status": "complete",
            "equity": 1_010_000.0,
            "cash": 900_000.0,
            "vault": 10_000.0,
            "known_market_value": 100_000.0,
        }

    monkeypatch.setattr(worker_equity, "get_sessionmaker", lambda: lambda: session)
    monkeypatch.setattr(worker_equity, "portfolio_valuation", valuation)
    now = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
    row = asyncio.run(persist_valuation_snapshot(ts=now))
    assert row is session.added[0]
    assert Decimal(str(row.equity)) == Decimal("1010000.0")
    assert session.committed is True
