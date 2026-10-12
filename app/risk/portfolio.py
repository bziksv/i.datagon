"""Risk: общая экспозиция и просадка портфеля."""

from decimal import Decimal

from app.book.orders import reject_order
from app.models import Order

GROSS_EXPOSURE_EXCEEDED = "gross_exposure"
MAX_DRAWDOWN_EXCEEDED = "max_drawdown"
DEFAULT_GROSS_LIMIT = Decimal("1")
DEFAULT_MAX_DRAWDOWN = Decimal("0.20")


def gate_portfolio(
    order: Order,
    *,
    price: Decimal,
    equity: Decimal,
    gross_existing: Decimal,
    max_drawdown: Decimal,
    gross_limit: Decimal = DEFAULT_GROSS_LIMIT,
    drawdown_limit: Decimal = DEFAULT_MAX_DRAWDOWN,
) -> Order:
    if Decimal(max_drawdown) >= Decimal(drawdown_limit):
        return reject_order(order, MAX_DRAWDOWN_EXCEEDED)
    proposed = Decimal(gross_existing) + Decimal(order.qty) * Decimal(price)
    if proposed / Decimal(equity) > Decimal(gross_limit):
        return reject_order(order, GROSS_EXPOSURE_EXCEEDED)
    return order
