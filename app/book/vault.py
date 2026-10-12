"""Сейф: 50% до перекрытия ввода, затем 20%."""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from app.book.accounts import TRADING_CASH, VAULT
from app.book.ledger import DEFAULT_DEPOSIT, ledger_balance
from app.models import LedgerEntry

PHASE_50 = Decimal("0.50")
PHASE_20 = Decimal("0.20")
VAULT_REASON = "vault"


def vault_cut(
    realized: Decimal,
    *,
    vault: Decimal,
    deposit: Decimal = DEFAULT_DEPOSIT,
) -> Decimal:
    pnl = Decimal(realized)
    held = Decimal(vault)
    cap = Decimal(deposit)
    if pnl <= 0:
        return Decimal("0")
    if held >= cap:
        return (pnl * PHASE_20).quantize(Decimal("0.01"))
    room = cap - held
    fill_need = room / PHASE_50
    if pnl <= fill_need:
        return (pnl * PHASE_50).quantize(Decimal("0.01"))
    rest = pnl - fill_need
    return (room + rest * PHASE_20).quantize(Decimal("0.01"))


def sweep(
    vault: Decimal,
    *,
    realized: Decimal = Decimal("0"),
    deposit: Decimal = DEFAULT_DEPOSIT,
) -> Decimal:
    return Decimal(vault) + vault_cut(realized, vault=vault, deposit=deposit)


def apply_closes(
    realized: Sequence[Decimal],
    *,
    deposit: Decimal = DEFAULT_DEPOSIT,
) -> Decimal:
    vault = Decimal("0")
    for pnl in realized:
        vault += vault_cut(pnl, vault=vault, deposit=deposit)
    return vault


def vault_entries(
    amount: Decimal,
    *,
    ts: datetime | None = None,
    ref: str | None = None,
) -> list[LedgerEntry]:
    cut = Decimal(amount)
    if cut <= 0:
        return []
    when = ts or datetime.now(UTC)
    return [
        LedgerEntry(
            account_kind=TRADING_CASH,
            amount=-cut,
            reason=VAULT_REASON,
            ref=ref,
            ts=when,
        ),
        LedgerEntry(
            account_kind=VAULT,
            amount=cut,
            reason=VAULT_REASON,
            ref=ref,
            ts=when,
        ),
    ]


def vault_balance(entries: Sequence[LedgerEntry]) -> Decimal:
    return ledger_balance(entries, VAULT)


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def vault_view(
    entries: Sequence[LedgerEntry],
    *,
    deposit: Decimal = DEFAULT_DEPOSIT,
) -> dict:
    accumulated = vault_balance(entries)
    cap = Decimal(deposit)
    remaining = cap - accumulated
    if remaining < 0:
        remaining = Decimal("0")
    phase = "20" if accumulated >= cap else "50"
    return {
        "deposit": _money(cap),
        "accumulated": _money(accumulated),
        "phase": phase,
        "remaining": _money(remaining),
    }
