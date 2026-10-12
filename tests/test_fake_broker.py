import inspect
from datetime import UTC, datetime
from decimal import Decimal

from app.broker.fake import FakeBroker
from app.broker.orders import place_order
from app.broker.port import BrokerPort, CandleBar, OrderRequest


def _bar(hour: int, close: str) -> CandleBar:
    price = Decimal(close)
    return CandleBar(
        ts=datetime(2026, 10, 12, hour, 0, tzinfo=UTC),
        o=price,
        h=price,
        low=price,
        c=price,
        v=Decimal("10"),
    )


def _run_sleeve(port: BrokerPort) -> int:
    """Минимальный шаг рукава: свечи + цена + ордер только через порт."""
    port.account()
    port.portfolio()
    bars = port.candles(figi="BBG004730N88", tf="1h", limit=2)
    quotes = port.prices(["SBER"])
    if len(bars) < 2 or not quotes:
        return 0
    if bars[-1].c <= bars[-2].c:
        return 0
    place_order(
        port,
        OrderRequest(
            ticker="SBER",
            side="buy",
            qty=1,
            type="market",
            client_order_id="c-sleeve-1",
        ),
    )
    return 1


def test_strategy_runs_without_tinkoff() -> None:
    source = inspect.getsource(FakeBroker) + inspect.getsource(_run_sleeve)
    assert "tinkoff" not in source
    broker = FakeBroker()
    broker.seed_price("SBER", Decimal("250.5"))
    broker.seed_candle("BBG004730N88", "1h", _bar(10, "249"))
    broker.seed_candle("BBG004730N88", "1h", _bar(11, "251"))
    assert _run_sleeve(broker) == 1
    assert len(broker._orders) == 1
    assert broker.portfolio().cash == Decimal("1000000")
