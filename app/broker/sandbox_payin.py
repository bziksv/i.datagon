"""SandboxPayIn: довести кэш до SANDBOX_DEPOSIT, если он ниже.

После пополнения в портфеле виден депозит (кэш >= deposit).
Если кэш уже не ниже — PayIn не вызываем.
"""

from collections.abc import Callable
from decimal import Decimal

DEFAULT_DEPOSIT = Decimal("1000000")


def payin_amount(cash: Decimal, deposit: Decimal = DEFAULT_DEPOSIT) -> Decimal | None:
    if cash >= deposit:
        return None
    return deposit - cash


def ensure_deposit(
    cash: Decimal,
    pay_in: Callable[[Decimal], None],
    deposit: Decimal = DEFAULT_DEPOSIT,
) -> Decimal:
    amount = payin_amount(cash, deposit)
    if amount is None:
        return cash
    pay_in(amount)
    return cash + amount
