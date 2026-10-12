from datetime import UTC, datetime
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.base import BarContext
from app.strategy.sma import SmaCrossStrategy
from app.strategy.stop import stop_hit


def _bar(low: str, close: str | None = None) -> CandleBar:
    price = Decimal(close or low)
    return CandleBar(
        ts=datetime(2026, 1, 10, tzinfo=UTC),
        o=price,
        h=price,
        low=Decimal(low),
        c=price,
        v=Decimal("10"),
    )


def test_exit_on_percent_stop() -> None:
    entry = Decimal("100")
    assert stop_hit(entry, Decimal("95")) is True
    assert stop_hit(entry, Decimal("96")) is False

    sleeve = SmaCrossStrategy(fast=2, slow=3)
    hit = BarContext(
        "SBER",
        [_bar("94")],
        entry_price=entry,
        side="buy",
    )
    assert sleeve.on_bar(hit).kind == "exit"

    hold = BarContext(
        "SBER",
        [_bar("96")],
        entry_price=entry,
        side="buy",
    )
    assert sleeve.on_bar(hold) is None
