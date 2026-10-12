from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.base import BarContext
from app.strategy.sma import SmaCrossStrategy


def _days(closes: list[str]) -> list[CandleBar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    bars = []
    for i, close in enumerate(closes):
        price = Decimal(close)
        bars.append(
            CandleBar(
                ts=start + timedelta(days=i),
                o=price,
                h=price,
                low=price,
                c=price,
                v=Decimal("10"),
            )
        )
    return bars


def test_sma_cross_buy_sell_flat() -> None:
    sleeve = SmaCrossStrategy(fast=2, slow=3)
    down = _days(["10", "9", "8", "7"])
    assert sleeve.on_bar(BarContext("SBER", down)).kind == "flat"

    buy = _days(["10", "9", "8", "7", "20"])
    assert sleeve.on_bar(BarContext("SBER", buy)).kind == "buy"

    sell = _days(["10", "11", "12", "13", "1"])
    assert sleeve.on_bar(BarContext("SBER", sell)).kind == "sell"


def test_not_enough_bars() -> None:
    sleeve = SmaCrossStrategy(fast=2, slow=3)
    assert sleeve.on_bar(BarContext("SBER", _days(["10", "11"]))) is None
