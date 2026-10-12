"""Проводки книги. Депозит 1 млн на trading_cash."""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.book.accounts import TRADING_CASH
from app.models import LedgerEntry

DEFAULT_DEPOSIT = Decimal("1000000")
DEPOSIT_REASON = "deposit"


def ledger_balance(
    entries: Sequence[LedgerEntry],
    account_kind: str = TRADING_CASH,
) -> Decimal:
    total = Decimal("0")
    for row in entries:
        if row.account_kind == account_kind:
            total += Decimal(str(row.amount))
    return total


def deposit_entry(
    existing: Sequence[LedgerEntry],
    deposit: Decimal = DEFAULT_DEPOSIT,
    *,
    ts: datetime | None = None,
    ref: str | None = "initial",
) -> LedgerEntry | None:
    balance = ledger_balance(existing, TRADING_CASH)
    gap = deposit - balance
    if gap <= 0:
        return None
    return LedgerEntry(
        account_kind=TRADING_CASH,
        amount=gap,
        reason=DEPOSIT_REASON,
        ref=ref,
        ts=ts or datetime.now(UTC),
    )


def apply_deposit(
    existing: Sequence[LedgerEntry],
    deposit: Decimal = DEFAULT_DEPOSIT,
    *,
    ts: datetime | None = None,
) -> tuple[LedgerEntry | None, Decimal]:
    entry = deposit_entry(existing, deposit, ts=ts)
    if entry is None:
        return None, ledger_balance(existing, TRADING_CASH)
    return entry, ledger_balance(existing, TRADING_CASH) + Decimal(str(entry.amount))


async def ensure_deposit(
    session: AsyncSession,
    deposit: Decimal = DEFAULT_DEPOSIT,
) -> Decimal:
    rows = list(
        await session.scalars(
            select(LedgerEntry).where(LedgerEntry.account_kind == TRADING_CASH)
        )
    )
    entry, balance = apply_deposit(rows, deposit)
    if entry is not None:
        session.add(entry)
        await session.flush()
    return balance


def ledger_item(row: LedgerEntry) -> dict:
    return {
        "account_kind": row.account_kind,
        "amount": float(Decimal(str(row.amount)).quantize(Decimal("0.01"))),
        "reason": row.reason,
        "ref": row.ref,
        "ts": row.ts.isoformat() if row.ts else None,
    }


def ledger_view(entries: Sequence[LedgerEntry]) -> dict:
    ordered = sorted(entries, key=lambda row: row.ts, reverse=True)
    return {"entries": [ledger_item(row) for row in ordered]}
