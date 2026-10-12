import inspect
from decimal import Decimal

from app.broker.sandbox_payin import DEFAULT_DEPOSIT, ensure_deposit, payin_amount
from app.broker.tinkoff import sandbox_pay_in_rub


def test_payin_when_cash_below_deposit() -> None:
    paid: list[Decimal] = []
    result = ensure_deposit(Decimal("0"), paid.append)
    assert paid == [DEFAULT_DEPOSIT]
    assert result == DEFAULT_DEPOSIT


def test_top_up_gap_only() -> None:
    paid: list[Decimal] = []
    result = ensure_deposit(Decimal("200000"), paid.append)
    assert paid == [Decimal("800000")]
    assert result == DEFAULT_DEPOSIT


def test_skip_when_cash_already_at_deposit() -> None:
    paid: list[Decimal] = []
    result = ensure_deposit(Decimal("1000000"), paid.append)
    assert paid == []
    assert result == Decimal("1000000")
    assert payin_amount(Decimal("1500000")) is None


def test_sdk_pay_in_uses_sandbox_pay_in() -> None:
    source = inspect.getsource(sandbox_pay_in_rub)
    assert "sandbox_pay_in" in source
    assert 'currency="rub"' in source
