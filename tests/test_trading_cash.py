from app.book.accounts import TRADING_CASH, account_kind, resolve_trading_cash
from app.models import Account


def test_opens_trading_cash_with_account_kind() -> None:
    first, created = resolve_trading_cash(None)
    assert created is True
    assert account_kind(first) == TRADING_CASH
    assert first.kind == "trading_cash"
    assert first.broker_account_id is None


def test_reuses_existing_trading_cash() -> None:
    existing = Account(kind=TRADING_CASH)
    first, created = resolve_trading_cash(existing)
    assert created is False
    assert first is existing
    again, created_again = resolve_trading_cash(first)
    assert created_again is False
    assert account_kind(again) == "trading_cash"
