"""Risk: один вход на тикер на бар."""

from collections.abc import Iterable

from app.book.orders import reject_order
from app.models import Order

ALREADY_ENTERED = "already_entered"


def already_entered(ticker: str, entered: Iterable[str]) -> bool:
    seen = {item.upper() for item in entered}
    return ticker.upper() in seen


def gate_once_per_bar(order: Order, entered: Iterable[str]) -> Order:
    if order.side != "buy":
        return order
    if already_entered(order.ticker, entered):
        return reject_order(order, ALREADY_ENTERED)
    return order
