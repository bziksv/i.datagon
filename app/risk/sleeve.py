"""Risk: вес рукава ≤ 40% equity."""

from decimal import Decimal

from app.book.orders import reject_order
from app.models import Order
from app.risk.name import name_notional, name_weight

DEFAULT_SLEEVE_SHARE = Decimal("0.40")
SLEEVE_WEIGHT_EXCEEDED = "sleeve_weight"


def gate_sleeve_weight(
    order: Order,
    *,
    price: Decimal,
    equity: Decimal,
    existing: Decimal = Decimal("0"),
    limit: Decimal = DEFAULT_SLEEVE_SHARE,
) -> Order:
    proposed = existing + name_notional(order.qty, price)
    if name_weight(proposed, equity) <= Decimal(limit):
        return order
    return reject_order(order, SLEEVE_WEIGHT_EXCEEDED)
