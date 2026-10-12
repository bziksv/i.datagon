"""Доходность капитала с отделением внешних денежных потоков."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from app.book.accounts import TRADING_CASH
from app.models import EquitySnapshot, LedgerEntry

EXTERNAL_FLOW_REASONS = frozenset({"deposit", "external_deposit", "withdrawal"})


def external_cash_flows(entries: Sequence[LedgerEntry]) -> list[LedgerEntry]:
    return sorted(
        (
            row
            for row in entries
            if row.account_kind == TRADING_CASH
            and row.reason in EXTERNAL_FLOW_REASONS
        ),
        key=lambda row: row.ts,
    )


def time_weighted_return(
    snapshots: Sequence[EquitySnapshot],
    entries: Sequence[LedgerEntry] = (),
) -> Decimal | None:
    """Compounds subperiod returns after removing dated external cash flows.

    Snapshot boundaries are the available valuation points. A flow in
    ``(previous.ts, current.ts]`` is removed from the end value.
    """
    rows = sorted(snapshots, key=lambda row: row.ts)
    if len(rows) < 2:
        return None
    flows = external_cash_flows(entries)
    compounded = Decimal("1")
    periods = 0
    for previous, current in zip(rows, rows[1:], strict=False):
        start = Decimal(str(previous.equity))
        end = Decimal(str(current.equity))
        if start <= 0:
            continue
        external = sum(
            (
                Decimal(str(flow.amount))
                for flow in flows
                if previous.ts < flow.ts <= current.ts
            ),
            Decimal("0"),
        )
        compounded *= Decimal("1") + (end - external - start) / start
        periods += 1
    return compounded - Decimal("1") if periods else None
