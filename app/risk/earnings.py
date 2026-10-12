"""Veto без ИИ: день отчёта / флаг в календаре — не входить."""

from collections.abc import Iterable, Mapping
from datetime import date

from app.book.orders import reject_order
from app.models import Order

EARNINGS_DAY = "earnings_day"


def on_earnings_day(
    ticker: str,
    day: date,
    calendar: Mapping[str, Iterable[date]],
) -> bool:
    marked = {item for item in calendar.get(ticker.upper(), ())}
    marked.update(calendar.get(ticker, ()))
    return day in marked


def gate_earnings(
    order: Order,
    calendar: Mapping[str, Iterable[date]],
    day: date,
) -> Order:
    if order.side != "buy":
        return order
    if on_earnings_day(order.ticker, day, calendar):
        return reject_order(order, EARNINGS_DAY)
    return order
