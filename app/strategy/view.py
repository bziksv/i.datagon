"""Сводка рукава для GET /sleeves/sma_cross."""

from collections.abc import Mapping, Sequence
from decimal import Decimal
from uuid import UUID

from app.alloc.view import ACTIVE_SLEEVES
from app.models import Position, SignalRow
from app.strategy.sma import SLEEVE

SIGNAL_LIMIT = 20


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def signal_item(row: SignalRow) -> dict:
    return {
        "sleeve": row.sleeve,
        "ticker": row.ticker,
        "ts": row.ts.isoformat(),
        "kind": row.kind,
        "payload": row.payload or {},
    }


def position_pnl(
    position: Position,
    mark: Decimal | None,
) -> Decimal:
    avg = Decimal(str(position.avg_price))
    price = mark if mark is not None else avg
    return Decimal(str(position.qty)) * (price - avg)


def position_item(
    position: Position,
    *,
    ticker: str | None = None,
    mark: Decimal | None = None,
) -> dict:
    avg = Decimal(str(position.avg_price))
    price = mark if mark is not None else avg
    return {
        "sleeve": position.sleeve,
        "instrument_id": str(position.instrument_id),
        "ticker": ticker,
        "qty": int(position.qty),
        "avg_price": _money(avg),
        "mark": _money(price),
        "unrealized": _money(position_pnl(position, mark)),
    }


def sleeve_view(
    signals: Sequence[SignalRow],
    positions: Sequence[Position],
    *,
    sleeve: str = SLEEVE,
    marks: Mapping[UUID, Decimal] | None = None,
    tickers: Mapping[UUID, str] | None = None,
    realized: Decimal = Decimal("0"),
) -> dict:
    prices = marks or {}
    names = tickers or {}
    rows = sorted(
        (row for row in signals if row.sleeve == sleeve),
        key=lambda row: row.ts,
        reverse=True,
    )
    held = [row for row in positions if row.sleeve == sleeve]
    unrealized = sum(
        (position_pnl(row, prices.get(row.instrument_id)) for row in held),
        Decimal("0"),
    )
    return {
        "sleeve": sleeve,
        "signals": [signal_item(row) for row in rows[:SIGNAL_LIMIT]],
        "positions": [
            position_item(
                row,
                ticker=names.get(row.instrument_id),
                mark=prices.get(row.instrument_id),
            )
            for row in held
        ],
        "pnl": {
            "realized": _money(realized),
            "unrealized": _money(unrealized),
            "total": _money(realized + unrealized),
        },
    }


def sleeves_view(
    signals: Sequence[SignalRow],
    positions: Sequence[Position],
    *,
    sleeves: Sequence[str] = ACTIVE_SLEEVES,
    marks: Mapping[UUID, Decimal] | None = None,
    realized: Mapping[str, Decimal] | None = None,
) -> dict:
    booked = realized or {}
    return {
        "sleeves": [
            {
                "sleeve": name,
                "pnl": sleeve_view(
                    signals,
                    positions,
                    sleeve=name,
                    marks=marks,
                    realized=booked.get(name, Decimal("0")),
                )["pnl"],
            }
            for name in sleeves
        ]
    }
