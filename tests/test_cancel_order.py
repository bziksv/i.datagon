import inspect

import pytest
from app.broker.orders import apply_cancel, cancel_order, place_order
from app.broker.port import BrokerPort, OrderAck, OrderRequest
from app.broker.tinkoff import cancel_sandbox_order
from app.models import Order


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
        return OrderAck(
            broker_order_id=broker_order_id,
            client_order_id="c-manual-1",
            status="cancelled",
        )

    def portfolio(self):  # type: ignore[override]
        raise NotImplementedError


def test_cancel_through_port_updates_our_status() -> None:
    port = _ManualPort()
    ack = place_order(
        port,
        OrderRequest(
            ticker="SBER",
            side="buy",
            qty=1,
            type="limit",
            client_order_id="c-manual-1",
        ),
    )
    row = Order(
        sleeve="manual",
        ticker="SBER",
        side="buy",
        qty=1,
        type="limit",
        status=ack.status,
        broker_order_id=ack.broker_order_id,
        client_order_id=ack.client_order_id,
    )
    cancelled = cancel_order(port, ack.broker_order_id)
    apply_cancel(row, cancelled)
    assert cancelled.status == "cancelled"
    assert row.status == "cancelled"
    assert row.broker_order_id == "ord-1"


def test_sdk_uses_sandbox_not_live_cancel() -> None:
    source = inspect.getsource(cancel_sandbox_order)
    assert "cancel_sandbox_order" in source
    assert "client.orders.cancel_order" not in source
    assert "sandbox.cancel_sandbox_order" in source


@pytest.mark.skip(reason="skip-live: sandbox cancel is not sent from tests")
def test_live_sandbox_cancel() -> None:
    raise AssertionError("must stay skipped")
