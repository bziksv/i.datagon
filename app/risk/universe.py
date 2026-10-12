"""Risk: тикер должен быть в активной вселенной."""

from collections.abc import Iterable, Sequence

from app.book.orders import reject_order
from app.models import Instrument, Order, UniverseMember

OUTSIDE_UNIVERSE = "outside_universe"


def in_universe(ticker: str, tickers: Iterable[str]) -> bool:
    allowed = {item.upper() for item in tickers}
    return ticker.upper() in allowed


def active_tickers(
    members: Sequence[UniverseMember],
    instruments: Sequence[Instrument],
) -> list[str]:
    by_id = {row.id: row for row in instruments}
    tickers: list[str] = []
    for member in members:
        if not member.active:
            continue
        instrument = by_id.get(member.instrument_id)
        if instrument is not None:
            tickers.append(instrument.ticker)
    return tickers


def gate_universe(order: Order, tickers: Iterable[str]) -> Order:
    if in_universe(order.ticker, tickers):
        return order
    return reject_order(order, OUTSIDE_UNIVERSE)


def gate_ticker(
    order: Order,
    members: Sequence[UniverseMember],
    instruments: Sequence[Instrument],
) -> Order:
    return gate_universe(order, active_tickers(members, instruments))
