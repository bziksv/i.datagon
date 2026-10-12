"""Единая рыночная оценка книги с явным качеством котировок."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.book.accounts import TRADING_CASH, VAULT
from app.book.ledger import ledger_balance
from app.book.returns import time_weighted_return
from app.models import EquitySnapshot, Fill, LedgerEntry, Position

VALUATION_VERSION = "v1-market-weighted-average"


@dataclass(frozen=True)
class PriceMark:
    instrument_id: UUID
    price: Decimal
    as_of: datetime
    source: str


def _money(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(Decimal(value).quantize(Decimal("0.01")))


def _max_drawdown(rows: Sequence[EquitySnapshot]) -> Decimal | None:
    values = [Decimal(str(row.equity)) for row in sorted(rows, key=lambda r: r.ts)]
    if not values:
        return None
    peak = values[0]
    worst = Decimal("0")
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value - peak) / peak)
    return abs(worst)


def value_portfolio(
    entries: Sequence[LedgerEntry],
    positions: Sequence[Position],
    marks: Mapping[UUID, PriceMark],
    *,
    fills: Sequence[Fill] = (),
    snapshots: Sequence[EquitySnapshot] = (),
    now: datetime | None = None,
    stale_after: timedelta = timedelta(hours=36),
) -> dict:
    """Returns equity only when every open position has a fresh valid mark."""
    observed_at = now or datetime.now(UTC)
    cash = ledger_balance(entries, TRADING_CASH)
    vault = ledger_balance(entries, VAULT)
    known_market_value = Decimal("0")
    total_cost = Decimal("0")
    missing = 0
    stale = 0
    valued: list[dict] = []

    for position in positions:
        qty = Decimal(str(position.qty))
        avg_price = Decimal(str(position.avg_price))
        avg_cost = Decimal(
            str(getattr(position, "avg_cost", None) or avg_price)
        )
        cost_basis = qty * avg_cost
        total_cost += cost_basis
        mark = marks.get(position.instrument_id)
        quality = "missing"
        market_value: Decimal | None = None
        unrealized: Decimal | None = None
        if mark is None or mark.price <= 0:
            missing += 1
        else:
            mark_as_of = (
                mark.as_of
                if mark.as_of.tzinfo is not None
                else mark.as_of.replace(tzinfo=UTC)
            )
            if observed_at - mark_as_of > stale_after:
                quality = "stale"
                stale += 1
            else:
                quality = "fresh"
                market_value = qty * Decimal(mark.price)
                unrealized = market_value - cost_basis
                known_market_value += market_value
        valued.append(
            {
                "sleeve": position.sleeve,
                "instrument_id": str(position.instrument_id),
                "qty": int(position.qty),
                "avg_price": _money(avg_price),
                "avg_cost": _money(avg_cost),
                "cost_basis": _money(cost_basis),
                "mark": _money(mark.price) if mark is not None else None,
                "mark_source": mark.source if mark is not None else None,
                "mark_as_of": mark.as_of.isoformat() if mark is not None else None,
                "mark_quality": quality,
                "market_value": _money(market_value),
                "unrealized_pnl": _money(unrealized),
            }
        )

    complete = missing == 0 and stale == 0
    equity = cash + vault + known_market_value if complete else None
    unrealized_total = known_market_value - total_cost if complete else None
    realized_gross = sum(
        (
            Decimal(str(row.realized_gross_pnl))
            for row in fills
            if getattr(row, "realized_gross_pnl", None) is not None
        ),
        Decimal("0"),
    )
    realized_net = sum(
        (
            Decimal(str(row.realized_net_pnl))
            for row in fills
            if getattr(row, "realized_net_pnl", None) is not None
        ),
        Decimal("0"),
    )
    costs = sum(
        (Decimal(str(getattr(row, "commission", 0) or 0)) for row in fills),
        Decimal("0"),
    )
    drawdown = _max_drawdown(snapshots)
    twr = time_weighted_return(snapshots, entries)
    return {
        "version": VALUATION_VERSION,
        "as_of": observed_at.isoformat(),
        "status": "complete" if complete else "partial",
        "cash": _money(cash),
        "vault": _money(vault),
        "known_market_value": _money(known_market_value),
        "positions_cost_basis": _money(total_cost),
        "equity": _money(equity),
        "realized_gross_pnl": _money(realized_gross),
        "realized_net_pnl": _money(realized_net),
        "unrealized_pnl": _money(unrealized_total),
        "trading_costs": _money(costs),
        "max_drawdown": float(drawdown) if drawdown is not None else None,
        "twr": float(twr) if twr is not None else None,
        "positions": valued,
        "data_quality": {
            "positions": len(positions),
            "fresh_marks": len(positions) - missing - stale,
            "missing_marks": missing,
            "stale_marks": stale,
            "stale_after_sec": int(stale_after.total_seconds()),
        },
    }
