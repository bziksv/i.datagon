from datetime import UTC, datetime
from decimal import Decimal

from app.book.orders import (
    BROKER_UNAVAILABLE,
    STATUS_FILLED,
    STATUS_NEW,
    STATUS_PARTIALLY_FILLED,
    STATUS_REJECTED,
    STATUS_UNKNOWN,
    accept_fill,
    draft_order,
    record_and_submit,
    submit_order,
)
from app.broker.fake import FakeBroker
from app.broker.port import OrderRequest
from app.models import Fill


def _req() -> OrderRequest:
    return OrderRequest(
        ticker="SBER",
        side="buy",
        qty=1,
        type="market",
        client_order_id="c-book-1",
    )


def test_draft_exists_before_broker() -> None:
    row = draft_order(_req(), sleeve="manual")
    assert row.status == STATUS_NEW
    assert row.broker_order_id is None
    assert row.client_order_id == "c-book-1"


def test_no_broker_rejects_with_reason() -> None:
    req = _req()
    row = draft_order(req, sleeve="manual")
    submit_order(row, None, req)
    assert row.status == STATUS_REJECTED
    assert row.raw["reject_reason"] == BROKER_UNAVAILABLE
    assert row.broker_order_id is None


def test_broker_error_rejects_meaningfully() -> None:
    class Boom(FakeBroker):
        def post_order(self, order):  # type: ignore[override]
            raise RuntimeError("sandbox down")

    row = record_and_submit(_req(), sleeve="manual", port=Boom())
    assert row.status == STATUS_REJECTED
    assert row.raw["reject_reason"] == "sandbox down"


def test_broker_timeout_is_unknown_not_rejected() -> None:
    class Timeout(FakeBroker):
        def post_order(self, order):  # type: ignore[override]
            raise TimeoutError("broker reply timed out")

    row = record_and_submit(_req(), sleeve="manual", port=Timeout())
    assert row.status == STATUS_UNKNOWN
    assert row.raw["broker_error"] == "broker reply timed out"


def test_fake_broker_keeps_new() -> None:
    row = record_and_submit(_req(), sleeve="manual", port=FakeBroker())
    assert row.status == "new"
    assert row.broker_order_id == "ord-1"


def test_same_client_order_id_skips_broker_and_second_fill() -> None:
    port = FakeBroker()
    req = _req()
    first = record_and_submit(req, sleeve="manual", port=port)
    second = record_and_submit(req, sleeve="manual", port=port, existing=first)
    assert second is first
    assert len(port._orders) == 1

    fill = Fill(
        order_id=first.id,
        qty=1,
        price=Decimal("250.5"),
        ts=datetime(2026, 10, 12, 10, 0, tzinfo=UTC),
        raw={"client_order_id": req.client_order_id},
    )
    assert accept_fill(first, [], fill) is fill
    replay = Fill(
        order_id=first.id,
        qty=1,
        price=Decimal("250.5"),
        ts=datetime(2026, 10, 12, 10, 1, tzinfo=UTC),
        raw={"client_order_id": req.client_order_id, "replay": True},
    )
    assert accept_fill(first, [fill], replay) is None


def test_distinct_partial_executions_are_accepted_once() -> None:
    order = draft_order(
        OrderRequest(
            ticker="SBER",
            side="buy",
            qty=10,
            type="market",
            client_order_id="c-partials",
        ),
        sleeve="manual",
    )
    first = Fill(
        order_id=order.id,
        execution_id="exec-1",
        qty=4,
        price=Decimal("100"),
        ts=datetime(2026, 10, 12, 10, 0, tzinfo=UTC),
        raw={},
    )
    second = Fill(
        order_id=order.id,
        execution_id="exec-2",
        qty=6,
        price=Decimal("101"),
        ts=datetime(2026, 10, 12, 10, 1, tzinfo=UTC),
        raw={},
    )
    duplicate = Fill(
        order_id=order.id,
        execution_id="exec-2",
        qty=6,
        price=Decimal("101"),
        ts=datetime(2026, 10, 12, 10, 2, tzinfo=UTC),
        raw={},
    )
    overflow = Fill(
        order_id=order.id,
        execution_id="exec-3",
        qty=1,
        price=Decimal("102"),
        ts=datetime(2026, 10, 12, 10, 3, tzinfo=UTC),
        raw={},
    )
    assert accept_fill(order, [], first) is first
    assert order.status == STATUS_PARTIALLY_FILLED
    assert accept_fill(order, [first], second) is second
    assert order.status == STATUS_FILLED
    assert accept_fill(order, [first, second], duplicate) is None
    assert accept_fill(order, [first, second], overflow) is None
