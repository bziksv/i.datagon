from decimal import Decimal

from app.book.orders import STATUS_NEW, STATUS_REJECTED, draft_order
from app.broker.port import OrderRequest
from app.models import Order
from app.risk.sleeve import SLEEVE_WEIGHT_EXCEEDED, gate_sleeve_weight


def _order(qty: int) -> Order:
    return draft_order(
        OrderRequest(
            ticker="SBER",
            side="buy",
            qty=qty,
            type="market",
            client_order_id=f"c-sleeve-{qty}",
        ),
        sleeve="sma_cross",
    )


def test_sleeve_weight_at_forty_percent_passes() -> None:
    gated = gate_sleeve_weight(
        _order(1600),
        price=Decimal("250"),
        equity=Decimal("1000000"),
    )
    assert gated.status == STATUS_NEW


def test_sleeve_weight_over_forty_percent_denied() -> None:
    gated = gate_sleeve_weight(
        _order(1601),
        price=Decimal("250"),
        equity=Decimal("1000000"),
    )
    assert gated.status == STATUS_REJECTED
    assert gated.raw["reject_reason"] == SLEEVE_WEIGHT_EXCEEDED
