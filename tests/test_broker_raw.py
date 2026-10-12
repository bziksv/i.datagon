from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.broker.raw import as_raw, attach_fill_raw, attach_order_raw, last_order_view
from app.models import Fill, Order


def _order(*, client_order_id: str, created_at: datetime, raw: dict | None = None) -> Order:
    return Order(
        sleeve="manual",
        ticker="SBER",
        side="buy",
        qty=1,
        type="limit",
        status="new",
        broker_order_id="ord-1",
        client_order_id=client_order_id,
        raw=raw or {},
        created_at=created_at,
    )


def test_as_raw_keeps_broker_chunk() -> None:
    payload = SimpleNamespace(
        order_id="ord-99",
        execution_report_status=SimpleNamespace(name="EXECUTION_REPORT_STATUS_NEW"),
        lots_requested=1,
    )
    raw = as_raw(payload)
    assert raw["order_id"] == "ord-99"
    assert raw["execution_report_status"] == "EXECUTION_REPORT_STATUS_NEW"
    assert raw["lots_requested"] == 1


def test_last_order_shows_raw() -> None:
    older = _order(
        client_order_id="c-old",
        created_at=datetime(2026, 10, 12, 9, 0, tzinfo=UTC),
        raw={"order_id": "stale"},
    )
    newer = _order(
        client_order_id="c-last",
        created_at=datetime(2026, 10, 12, 10, 0, tzinfo=UTC),
    )
    attach_order_raw(
        newer,
        SimpleNamespace(order_id="ord-1", figi="BBG004730N88"),
    )
    view = last_order_view([older, newer])
    assert view["client_order_id"] == "c-last"
    assert view["raw"]["order_id"] == "ord-1"
    assert view["raw"]["figi"] == "BBG004730N88"


def test_fill_keeps_raw() -> None:
    fill = Fill(
        order_id=uuid4(),
        qty=1,
        price=250.5,
        ts=datetime(2026, 10, 12, 10, 0, tzinfo=UTC),
        raw={},
    )
    attach_fill_raw(fill, {"order_id": "ord-1", "price": "250.5"})
    assert fill.raw["order_id"] == "ord-1"
    assert fill.raw["price"] == "250.5"
