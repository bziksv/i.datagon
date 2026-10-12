"""Применение fill: позиция и проводка в ledger."""

from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID, uuid4

from app.book.accounts import TRADING_CASH
from app.models import Fill, LedgerEntry, Position

FILL_REASON = "fill"


def apply_fill(
    position: Position | None,
    fill: Fill,
    *,
    sleeve: str,
    instrument_id: UUID,
    side: str,
    ref: str | None = None,
) -> tuple[Position, LedgerEntry]:
    qty = int(fill.qty)
    price = Decimal(str(fill.price))
    notional = Decimal(qty) * price
    row = position or Position(
        id=uuid4(),
        sleeve=sleeve,
        instrument_id=instrument_id,
        qty=0,
        avg_price=Decimal("0"),
    )
    current_qty = int(row.qty)
    current_avg = Decimal(str(row.avg_price))
    current_avg_cost = Decimal(
        str(getattr(row, "avg_cost", None) or current_avg)
    )
    commission = Decimal(str(getattr(fill, "commission", 0) or 0))
    if side.lower() == "buy":
        new_qty = current_qty + qty
        row.avg_price = (
            (current_avg * current_qty + notional) / new_qty
            if new_qty
            else Decimal("0")
        )
        row.avg_cost = (
            (
                current_avg_cost * current_qty
                + notional
                + commission
            )
            / new_qty
            if new_qty
            else Decimal("0")
        )
        row.qty = new_qty
        amount = -notional
    else:
        if qty > current_qty:
            raise ValueError("fill quantity exceeds position")
        fill.realized_gross_pnl = (price - current_avg) * qty
        fill.realized_net_pnl = (
            (price - current_avg_cost) * qty - commission
        )
        row.qty = current_qty - qty
        if row.qty == 0:
            row.avg_price = Decimal("0")
            row.avg_cost = Decimal("0")
        amount = notional
    return row, LedgerEntry(
        account_kind=TRADING_CASH,
        amount=amount,
        reason=FILL_REASON,
        ref=ref or str(fill.order_id),
        ts=fill.ts,
    )


def apply_fills(
    position: Position | None,
    fills: Sequence[Fill],
    *,
    sleeve: str,
    instrument_id: UUID,
    side: str,
    ref: str | None = None,
) -> tuple[Position | None, list[LedgerEntry]]:
    row = position
    entries: list[LedgerEntry] = []
    for fill in fills:
        row, entry = apply_fill(
            row,
            fill,
            sleeve=sleeve,
            instrument_id=instrument_id,
            side=side,
            ref=ref,
        )
        entries.append(entry)
    return row, entries
