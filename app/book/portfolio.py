"""Сводка портфеля для GET /portfolio."""

from collections.abc import Sequence
from decimal import Decimal

from app.book.accounts import TRADING_CASH
from app.book.commission import compute_equity, positions_value
from app.book.ledger import ledger_balance
from app.models import LedgerEntry, Position


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def position_item(row: Position) -> dict:
    return {
        "sleeve": row.sleeve,
        "instrument_id": str(row.instrument_id),
        "qty": int(row.qty),
        "avg_price": _money(Decimal(str(row.avg_price))),
    }


def portfolio_view(
    *,
    cash: Decimal,
    vault: Decimal = Decimal("0"),
    positions: Sequence[Position] = (),
) -> dict:
    value = sum((positions_value(row) for row in positions), Decimal("0"))
    return {
        "cash": _money(cash),
        "vault": _money(vault),
        "positions": [position_item(row) for row in positions],
        "equity": _money(compute_equity(cash, vault, value)),
    }


def portfolio_from_book(
    entries: Sequence[LedgerEntry],
    positions: Sequence[Position],
    *,
    vault: Decimal = Decimal("0"),
) -> dict:
    return portfolio_view(
        cash=ledger_balance(entries, TRADING_CASH),
        vault=vault,
        positions=positions,
    )
