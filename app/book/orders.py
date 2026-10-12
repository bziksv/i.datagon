"""Ордер сначала в нашей книге, потом к брокеру."""

from collections.abc import Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.broker.port import BrokerPort, OrderRequest
from app.models import Fill, Order

STATUS_NEW = "new"
STATUS_REJECTED = "rejected"
BROKER_UNAVAILABLE = "broker_unavailable"


def draft_order(request: OrderRequest, *, sleeve: str) -> Order:
    return Order(
        id=uuid4(),
        sleeve=sleeve,
        ticker=request.ticker,
        side=request.side,
        qty=request.qty,
        type=request.type,
        status=STATUS_NEW,
        broker_order_id=None,
        client_order_id=request.client_order_id,
        raw={},
    )


def reject_order(order: Order, reason: str) -> Order:
    order.status = STATUS_REJECTED
    raw = dict(order.raw or {})
    raw["reject_reason"] = reason
    order.raw = raw
    return order


def submit_order(
    order: Order,
    port: BrokerPort | None,
    request: OrderRequest,
) -> Order:
    if port is None:
        return reject_order(order, BROKER_UNAVAILABLE)
    try:
        ack = port.post_order(request)
    except Exception as exc:
        return reject_order(order, str(exc) or "broker_error")
    order.status = ack.status
    order.broker_order_id = ack.broker_order_id
    return order


def reuse_order(existing: Order | None, request: OrderRequest) -> Order | None:
    if existing is not None and existing.client_order_id == request.client_order_id:
        return existing
    return None


def record_and_submit(
    request: OrderRequest,
    *,
    sleeve: str,
    port: BrokerPort | None,
    existing: Order | None = None,
) -> Order:
    reused = reuse_order(existing, request)
    if reused is not None:
        return reused
    order = draft_order(request, sleeve=sleeve)
    return submit_order(order, port, request)


def accept_fill(
    order: Order,
    existing_fills: Sequence[Fill],
    fill: Fill,
) -> Fill | None:
    """Повтор с тем же client_order_id не даёт второй fill."""
    if any(row.order_id == order.id for row in existing_fills):
        return None
    return fill


async def load_order_by_client_id(
    session: AsyncSession,
    client_order_id: str,
) -> Order | None:
    return await session.scalar(
        select(Order).where(Order.client_order_id == client_order_id)
    )


def order_item(order: Order) -> dict:
    raw = dict(order.raw or {})
    return {
        "id": str(order.id),
        "sleeve": order.sleeve,
        "ticker": order.ticker,
        "side": order.side,
        "qty": order.qty,
        "type": order.type,
        "status": order.status,
        "broker_order_id": order.broker_order_id,
        "client_order_id": order.client_order_id,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "reject_reason": raw.get("reject_reason"),
        "raw": raw,
    }


def orders_view(
    orders: Sequence[Order],
    *,
    status: str | None = None,
) -> dict:
    rows = [
        order
        for order in orders
        if status is None or order.status == status
    ]
    return {"orders": [order_item(order) for order in rows]}
