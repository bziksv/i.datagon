from datetime import UTC, datetime
from decimal import Decimal

from app.book.accounts import TRADING_CASH
from app.book.ledger import DEFAULT_DEPOSIT, apply_deposit, ledger_balance
from app.models import LedgerEntry


def test_deposit_one_million_balances() -> None:
    entry, balance = apply_deposit([])
    assert entry is not None
    assert entry.account_kind == TRADING_CASH
    assert entry.reason == "deposit"
    assert Decimal(str(entry.amount)) == DEFAULT_DEPOSIT
    assert balance == Decimal("1000000")
    assert ledger_balance([entry]) == Decimal("1000000")


def test_repeat_deposit_does_not_double() -> None:
    first, balance = apply_deposit([])
    assert first is not None
    again, again_balance = apply_deposit([first])
    assert again is None
    assert again_balance == Decimal("1000000")
    assert ledger_balance([first]) == balance


def test_top_up_gap_to_one_million() -> None:
    partial = LedgerEntry(
        account_kind=TRADING_CASH,
        amount=Decimal("400000"),
        reason="deposit",
        ref="partial",
        ts=datetime(2026, 10, 12, tzinfo=UTC),
    )
    entry, balance = apply_deposit([partial])
    assert entry is not None
    assert Decimal(str(entry.amount)) == Decimal("600000")
    assert balance == Decimal("1000000")
    assert ledger_balance([partial, entry]) == Decimal("1000000")
