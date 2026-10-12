from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.base import BarContext
from app.strategy.donchian import DonchianBreakoutStrategy


def _bars(rows: list[tuple[str, str, str]]) -> list[CandleBar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    bars = []
    for i, (high, low, close) in enumerate(rows):
        bars.append(
            CandleBar(
                ts=start + timedelta(days=i),
                o=Decimal(close),
                h=Decimal(high),
                low=Decimal(low),
                c=Decimal(close),
                v=Decimal("10"),
            )
        )
    return bars


def test_donchian_buy_sell_flat() -> None:
    sleeve = DonchianBreakoutStrategy(period=2)
    flat = _bars(
        [
            ("10", "8", "9"),
            ("11", "9", "10"),
            ("11", "9", "10"),
        ]
    )
    assert sleeve.on_bar(BarContext("SBER", flat)).kind == "flat"
    assert sleeve.on_bar(BarContext("SBER", flat)).sleeve == "donchian_breakout"

    buy = _bars(
        [
            ("10", "8", "9"),
            ("11", "9", "10"),
            ("14", "10", "13"),
        ]
    )
    assert sleeve.on_bar(BarContext("SBER", buy)).kind == "buy"

    sell = _bars(
        [
            ("10", "8", "9"),
            ("11", "9", "10"),
            ("10", "6", "7"),
        ]
    )
    assert sleeve.on_bar(BarContext("SBER", sell)).kind == "sell"


def test_donchian_not_enough_bars() -> None:
    sleeve = DonchianBreakoutStrategy(period=2)
    assert sleeve.on_bar(BarContext("SBER", _bars([("10", "9", "10")]))) is None
