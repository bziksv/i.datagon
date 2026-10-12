"""Фиксированный процентный стоп в правиле рукава."""

from decimal import Decimal

from app.broker.port import CandleBar

DEFAULT_STOP_PCT = Decimal("0.05")


def stop_price(
    entry: Decimal,
    *,
    side: str = "buy",
    stop_pct: Decimal = DEFAULT_STOP_PCT,
) -> Decimal:
    share = Decimal(stop_pct)
    if side == "sell":
        return Decimal(entry) * (Decimal("1") + share)
    return Decimal(entry) * (Decimal("1") - share)


def stop_hit(
    entry: Decimal,
    last: Decimal,
    *,
    side: str = "buy",
    stop_pct: Decimal = DEFAULT_STOP_PCT,
) -> bool:
    level = stop_price(entry, side=side, stop_pct=stop_pct)
    if side == "sell":
        return Decimal(last) >= level
    return Decimal(last) <= level


def bar_hits_stop(
    bar: CandleBar,
    entry: Decimal,
    *,
    side: str = "buy",
    stop_pct: Decimal = DEFAULT_STOP_PCT,
) -> bool:
    last = bar.h if side == "sell" else bar.low
    return stop_hit(entry, last, side=side, stop_pct=stop_pct)
