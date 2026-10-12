"""Снимок equity по расписанию воркера."""

from datetime import datetime
from decimal import Decimal

from app.book.equity import make_snapshot
from app.models import EquitySnapshot

SNAPSHOT_INTERVAL_SEC = 3600


def snapshot_due(
    last: datetime | None,
    now: datetime,
    interval: int = SNAPSHOT_INTERVAL_SEC,
) -> bool:
    if last is None:
        return True
    return (now - last).total_seconds() >= interval


def take_snapshot(
    *,
    trading_cash: Decimal,
    vault: Decimal = Decimal("0"),
    positions_value: Decimal = Decimal("0"),
    ts: datetime | None = None,
) -> EquitySnapshot:
    return make_snapshot(
        trading_cash=trading_cash,
        vault=vault,
        positions_value=positions_value,
        ts=ts,
    )


def record_snapshot(
    rows: list[EquitySnapshot],
    snapshot: EquitySnapshot,
) -> list[EquitySnapshot]:
    rows.append(snapshot)
    return rows
