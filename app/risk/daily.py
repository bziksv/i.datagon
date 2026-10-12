"""Risk: дневной убыток сверх порога — новые входы запрещены."""

from decimal import Decimal

from app.book.orders import reject_order
from app.models import Order

DEFAULT_DAILY_LOSS = Decimal("0.03")
DAILY_LOSS_EXCEEDED = "daily_loss"


def daily_loss_share(start_equity: Decimal, equity: Decimal) -> Decimal:
    start = Decimal(start_equity)
    if start <= 0:
        return Decimal("0")
    lost = start - Decimal(equity)
    if lost <= 0:
        return Decimal("0")
    return lost / start


def gate_daily_loss(
    order: Order,
    *,
    start_equity: Decimal,
    equity: Decimal,
    limit: Decimal = DEFAULT_DAILY_LOSS,
) -> Order:
    if daily_loss_share(start_equity, equity) <= Decimal(limit):
        return order
    if order.side != "buy":
        return order
    return reject_order(order, DAILY_LOSS_EXCEEDED)
