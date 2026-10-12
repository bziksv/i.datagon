from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.base import BarContext
from app.strategy.rsi import RsiReversionStrategy, wilder_rsi


def _bars(closes: list[float]) -> list[CandleBar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    out = []
    for i, close in enumerate(closes):
        price = Decimal(str(close))
        out.append(
            CandleBar(
                ts=start + timedelta(days=i),
                o=price,
                h=price,
                low=price,
                c=price,
                v=Decimal("10"),
            )
        )
    return out


def test_rsi_buy_oversold_sell_overbought() -> None:
    # падение → RSI низкий → buy; рост → RSI высокий → sell
    down = [100 - i for i in range(20)]
    sleeve = RsiReversionStrategy(period=5, oversold=Decimal("40"), overbought=Decimal("60"))
    buy = sleeve.on_bar(BarContext("SBER", _bars(down)))
    assert buy is not None
    assert buy.kind == "buy"
    assert buy.sleeve == "rsi_reversion"

    up = [50 + i * 3 for i in range(20)]
    sell = sleeve.on_bar(BarContext("SBER", _bars(up)))
    assert sell is not None
    assert sell.kind == "sell"


def test_rsi_not_enough_bars() -> None:
    sleeve = RsiReversionStrategy(period=14)
    assert sleeve.on_bar(BarContext("SBER", _bars([1, 2, 3]))) is None


def test_wilder_rsi_bounds() -> None:
    closes = [Decimal(str(x)) for x in range(1, 20)]
    value = wilder_rsi(closes, 5)
    assert value is not None
    assert Decimal("0") <= value <= Decimal("100")
