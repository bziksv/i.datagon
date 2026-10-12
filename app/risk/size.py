"""Risk: потенциальный убыток позиции ограничен долей equity."""

from decimal import Decimal

from app.book.orders import reject_order
from app.models import Order

TRADE_RISK_EXCEEDED = "trade_risk_limit"
DEFAULT_TRADE_RISK_SHARE = Decimal("0.005")
DEFAULT_ROUND_TRIP_COST_BPS = Decimal("10")


def gate_trade_risk(
    order: Order,
    *,
    price: Decimal,
    stop_price: Decimal,
    equity: Decimal,
    limit: Decimal = DEFAULT_TRADE_RISK_SHARE,
    round_trip_cost_bps: Decimal = DEFAULT_ROUND_TRIP_COST_BPS,
) -> Order:
    risk_per_share = Decimal(price) - Decimal(stop_price)
    estimated_cost = (
        Decimal(order.qty)
        * Decimal(price)
        * Decimal(round_trip_cost_bps)
        / Decimal("10000")
    )
    risk = Decimal(order.qty) * risk_per_share + estimated_cost
    if risk <= Decimal(equity) * Decimal(limit):
        return order
    return reject_order(order, TRADE_RISK_EXCEEDED)
