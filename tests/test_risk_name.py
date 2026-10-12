from decimal import Decimal

from app.book.orders import STATUS_NEW, STATUS_REJECTED, draft_order
from app.broker.port import OrderRequest
from app.models import Order
from app.risk.name import NAME_WEIGHT_EXCEEDED, gate_name_weight


def _order(qty: int) -> Order:
    return draft_order(
        OrderRequest(
            ticker="SBER",
            side="buy",
            qty=qty,
            type="market",
            client_order_id=f"c-name-{qty}",
        ),
        sleeve="sma_cross",
    )


def test_name_weight_at_ten_percent_passes() -> None:
    gated = gate_name_weight(
        _order(400),
        price=Decimal("250"),
        equity=Decimal("1000000"),
    )
    assert gated.status == STATUS_NEW


def test_name_weight_over_ten_percent_denied() -> None:
    gated = gate_name_weight(
        _order(401),
        price=Decimal("250"),
        equity=Decimal("1000000"),
    )
    assert gated.status == STATUS_REJECTED
    assert gated.raw["reject_reason"] == NAME_WEIGHT_EXCEEDED
