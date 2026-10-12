"""Типизированные денежные события книги."""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from app.book.accounts import TRADING_CASH
from app.models import LedgerEntry

EXPENSE_REASONS = frozenset({"commission", "fee", "tax"})
INCOME_REASONS = frozenset({"dividend"})
EXTERNAL_REASONS = frozenset({"deposit", "withdrawal"})
BOOK_EVENT_REASONS = EXPENSE_REASONS | INCOME_REASONS | EXTERNAL_REASONS


def cash_event(
    reason: str,
    amount: Decimal,
    *,
    ref: str | None = None,
    ts: datetime | None = None,
) -> LedgerEntry:
    kind = reason.strip().lower()
    if kind not in BOOK_EVENT_REASONS:
        raise ValueError("unsupported cash event")
    value = abs(Decimal(amount))
    if kind in EXPENSE_REASONS or kind == "withdrawal":
        value = -value
    return LedgerEntry(
        account_kind=TRADING_CASH,
        amount=value,
        reason=kind,
        ref=ref,
        ts=ts or datetime.now(UTC),
    )


def cash_event_summary(entries: Sequence[LedgerEntry]) -> dict[str, float]:
    totals = {
        reason: Decimal("0")
        for reason in sorted(BOOK_EVENT_REASONS)
    }
    for row in entries:
        if row.reason in totals:
            totals[row.reason] += Decimal(str(row.amount))
    return {
        reason: float(value.quantize(Decimal("0.01")))
        for reason, value in totals.items()
    }
