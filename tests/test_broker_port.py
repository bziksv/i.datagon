from datetime import UTC, datetime
from decimal import Decimal

from app.broker.fake import FakeBroker
from app.broker.port import (
    BrokerPort,
    CandleBar,
    LastPrice,
    OrderRequest,
)


def _bar() -> CandleBar:
    return CandleBar(
        ts=datetime(2026, 10, 12, 10, 0, tzinfo=UTC),
        o=Decimal("100"),
        h=Decimal("101"),
        low=Decimal("99"),
        c=Decimal("100.5"),
        v=Decimal("10"),
    )


def test_fake_is_broker_port() -> None:
    assert isinstance(FakeBroker(), BrokerPort)


def test_account() -> None:
    assert FakeBroker().account().broker_account_id == "sbx-1"


def test_candles() -> None:
    broker = FakeBroker()
    bar = _bar()
    broker.seed_candle("BBG000", "1h", bar)
    assert broker.candles(figi="BBG000", tf="1h") == [bar]


def test_prices() -> None:
    broker = FakeBroker()
    broker.seed_price("SBER", Decimal("250.5"))
    got = broker.prices(["SBER", "GAZP"])
    assert got == [LastPrice(ticker="SBER", price=Decimal("250.5"))]


def test_post_order_and_cancel() -> None:
    broker = FakeBroker()
    ack = broker.post_order(
        OrderRequest(
            ticker="SBER",
            side="buy",
            qty=1,
            type="market",
            client_order_id="c1",
        )
    )
    assert ack.status == "new"
    assert ack.client_order_id == "c1"
    cancelled = broker.cancel(ack.broker_order_id)
    assert cancelled.status == "cancelled"
    assert cancelled.broker_order_id == ack.broker_order_id


def test_portfolio() -> None:
    port = FakeBroker().portfolio()
    assert port.currency == "RUB"
    assert port.cash == Decimal("1000000")
    assert port.positions == ()
