"""Комиссия fill: поле и вычет из cash, даже если 0."""

from decimal import Decimal

from app.book.accounts import TRADING_CASH
from app.models import Fill, LedgerEntry, Position

COMMISSION_REASON = "commission"


def commission_of(fill: Fill) -> Decimal:
    value = getattr(fill, "commission", None)
    if value is None:
        value = (fill.raw or {}).get("commission", 0)
    return Decimal(str(value or 0))


def commission_entry(fill: Fill, *, ref: str | None = None) -> LedgerEntry:
    return LedgerEntry(
        account_kind=TRADING_CASH,
        amount=-commission_of(fill),
        reason=COMMISSION_REASON,
        ref=ref or str(fill.order_id),
        ts=fill.ts,
    )


def positions_value(position: Position) -> Decimal:
    return Decimal(str(position.qty)) * Decimal(str(position.avg_price))


def compute_equity(
    trading_cash: Decimal,
    vault: Decimal,
    positions_value: Decimal,
) -> Decimal:
    return trading_cash + vault + positions_value
