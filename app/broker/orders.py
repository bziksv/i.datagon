"""Ордера только через порт. Стратегия сюда не ходит."""

from app.broker.port import BrokerPort, OrderAck, OrderRequest
from app.models import Order


def place_order(port: BrokerPort, order: OrderRequest) -> OrderAck:
    return port.post_order(order)


def cancel_order(port: BrokerPort, broker_order_id: str) -> OrderAck:
    return port.cancel(broker_order_id)


def apply_cancel(order: Order, ack: OrderAck) -> Order:
    """Наш статус после отмены у брокера."""
    order.status = ack.status
    if ack.broker_order_id:
        order.broker_order_id = ack.broker_order_id
    return order
