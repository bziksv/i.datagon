"""Два рукава на одних свечах: отдельный book в positions.sleeve."""

from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID, uuid4

from app.book.positions import apply_fill
from app.broker.port import CandleBar
from app.models import Fill, Position
from app.strategy.base import BarContext, Signal, Strategy


def _fill(qty: int, price: Decimal, ts) -> Fill:
    return Fill(
        order_id=uuid4(),
        qty=qty,
        price=price,
        ts=ts,
        raw={},
    )


def apply_signal_fill(
    position: Position | None,
    signal: Signal,
    *,
    instrument_id: UUID,
    qty: int,
    price: Decimal,
) -> Position | None:
    if signal.kind == "buy" and (position is None or int(position.qty) == 0):
        row, _ = apply_fill(
            position,
            _fill(qty, price, signal.ts),
            sleeve=signal.sleeve,
            instrument_id=instrument_id,
            side="buy",
        )
        return row
    if signal.kind in {"sell", "exit"} and position is not None and int(position.qty) > 0:
        row, _ = apply_fill(
            position,
            _fill(int(position.qty), price, signal.ts),
            sleeve=signal.sleeve,
            instrument_id=instrument_id,
            side="sell",
        )
        return row
    return position


def run_parallel(
    strategies: Sequence[Strategy],
    ticker: str,
    bars: Sequence[CandleBar],
    *,
    instrument_id: UUID,
    qty: int = 1,
) -> dict[str, Position]:
    books: dict[str, Position | None] = {strategy.sleeve: None for strategy in strategies}
    for end in range(1, len(bars) + 1):
        bar = bars[end - 1]
        for strategy in strategies:
            held = books[strategy.sleeve]
            ctx = BarContext(
                ticker,
                bars[:end],
                entry_price=(
                    Decimal(str(held.avg_price)) if held and int(held.qty) else None
                ),
            )
            signal = strategy.on_bar(ctx)
            if signal is None:
                continue
            books[strategy.sleeve] = apply_signal_fill(
                held,
                signal,
                instrument_id=instrument_id,
                qty=qty,
                price=bar.c,
            )
    return {sleeve: row for sleeve, row in books.items() if row is not None}
