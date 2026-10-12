from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.base import BarContext
from app.strategy.scalp import EmaScalpStrategy


def _bars(closes: list[float]) -> list[CandleBar]:
    start = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
    out = []
    for i, close in enumerate(closes):
        price = Decimal(str(close))
        out.append(
            CandleBar(
                ts=start + timedelta(minutes=15 * i),
                o=price,
                h=price,
                low=price,
                c=price,
                v=Decimal("10"),
            )
        )
    return out


def test_ema_scalp_cross() -> None:
    sleeve = EmaScalpStrategy(fast=2, slow=3)
    # down then sharp up → fast crosses above slow
    closes = [10, 9, 8, 7, 6, 12, 13, 14]
    signal = sleeve.on_bar(BarContext("SBER", _bars(closes)))
    assert signal is not None
    assert signal.sleeve == "ema_scalp"
    assert signal.kind in {"buy", "sell", "flat"}
    assert sleeve.timeframe == "15m"


def test_ema_scalp_not_enough() -> None:
    sleeve = EmaScalpStrategy(fast=2, slow=3)
    assert sleeve.on_bar(BarContext("SBER", _bars([1, 2]))) is None


def test_ema_scalp_stop_exit() -> None:
    sleeve = EmaScalpStrategy(fast=2, slow=3, stop_pct=Decimal("0.05"))
    bars = _bars([100, 100, 100, 100, 90])
    signal = sleeve.on_bar(
        BarContext("SBER", bars, entry_price=Decimal("100"), side="buy")
    )
    assert signal is not None
    assert signal.kind == "exit"
