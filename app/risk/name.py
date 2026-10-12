"""Risk: вес имени ≤ 10% equity."""

from decimal import Decimal

from app.book.orders import reject_order
from app.models import Order
from app.strategy.size import DEFAULT_NAME_SHARE

NAME_WEIGHT_EXCEEDED = "name_weight"


def name_notional(qty: int, price: Decimal) -> Decimal:
    return Decimal(qty) * Decimal(price)


def name_weight(notional: Decimal, equity: Decimal) -> Decimal:
    if equity <= 0:
        return Decimal("1")
    return Decimal(notional) / Decimal(equity)


def gate_name_weight(
    order: Order,
    *,
    price: Decimal,
    equity: Decimal,
    existing: Decimal = Decimal("0"),
    limit: Decimal = DEFAULT_NAME_SHARE,
) -> Order:
    proposed = existing + name_notional(order.qty, price)
    if name_weight(proposed, equity) <= Decimal(limit):
        return order
    return reject_order(order, NAME_WEIGHT_EXCEEDED)
