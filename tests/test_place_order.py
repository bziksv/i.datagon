import inspect
from pathlib import Path

import pytest
from app.broker.orders import place_order
from app.broker.port import BrokerPort, OrderAck, OrderRequest
from app.broker.tinkoff import post_sandbox_order


class _ManualPort(BrokerPort):
    def account(self):  # type: ignore[override]
        raise NotImplementedError

    def candles(self, **kwargs):  # type: ignore[override]
        raise NotImplementedError

    def prices(self, tickers):  # type: ignore[override]
        raise NotImplementedError

    def post_order(self, order: OrderRequest) -> OrderAck:
        return OrderAck(
            broker_order_id="ord-1",
            client_order_id=order.client_order_id,
            status="new",
        )

    def cancel(self, broker_order_id: str) -> OrderAck:
        raise NotImplementedError

    def portfolio(self):  # type: ignore[override]
        raise NotImplementedError


def test_place_order_through_port() -> None:
    port = _ManualPort()
    ack = place_order(
        port,
        OrderRequest(
            ticker="SBER",
            side="buy",
            qty=1,
            type="market",
            client_order_id="c-manual-1",
        ),
    )
    assert ack.client_order_id == "c-manual-1"
    assert ack.broker_order_id
    assert ack.status == "new"


def test_sdk_uses_sandbox_not_live_orders() -> None:
    source = inspect.getsource(post_sandbox_order)
    assert "post_sandbox_order" in source
    assert "client.orders.post_order" not in source
    assert "sandbox.post_sandbox_order" in source


def test_no_strategy_module_posts_orders() -> None:
    root = Path(__file__).resolve().parents[1]
    offenders = []
    for path in (root / "app").rglob("*.py"):
        if set(path.parts) & {"broker", "book", "risk"}:
            continue
        text = path.read_text()
        if "place_order" in text or "post_order" in text:
            offenders.append(str(path.relative_to(root)))
    for path in (root / "worker").rglob("*.py"):
        text = path.read_text()
        if "place_order" in text or "post_order" in text:
            offenders.append(str(path.relative_to(root)))
    assert offenders == []


@pytest.mark.skip(reason="skip-live: sandbox order is not sent from tests")
def test_live_sandbox_order() -> None:
    raise AssertionError("must stay skipped")
