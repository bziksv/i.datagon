from decimal import Decimal

from app.book.accounts import VAULT
from app.book.ledger import DEFAULT_DEPOSIT, ledger_balance
from app.book.vault import apply_closes, vault_cut, vault_entries


def test_series_of_closes_sends_half_to_vault() -> None:
    vault = apply_closes(
        [Decimal("10000"), Decimal("20000"), Decimal("40000")],
        deposit=DEFAULT_DEPOSIT,
    )
    assert vault == Decimal("35000")
    assert vault < DEFAULT_DEPOSIT
    assert vault_cut(Decimal("10000"), vault=Decimal("0")) == Decimal("5000")
    assert vault_cut(Decimal("-3000"), vault=Decimal("0")) == Decimal("0")


def test_vault_ledger_moves_from_cash() -> None:
    rows = vault_entries(Decimal("5000"), ref="close-1")
    assert [row.account_kind for row in rows] == ["trading_cash", VAULT]
    assert ledger_balance(rows, "trading_cash") == Decimal("-5000")
    assert ledger_balance(rows, VAULT) == Decimal("5000")
