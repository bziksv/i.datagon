from decimal import Decimal

from app.book.orders import STATUS_NEW, STATUS_REJECTED, draft_order
from app.broker.port import OrderRequest
from app.models import Order
from app.risk.daily import DAILY_LOSS_EXCEEDED, gate_daily_loss


def _order(side: str) -> Order:
    return draft_order(
        OrderRequest(
            ticker="SBER",
            side=side,
            qty=1,
            type="market",
            client_order_id=f"c-daily-{side}",
        ),
        sleeve="sma_cross",
    )


def test_daily_loss_under_limit_allows_entry() -> None:
    gated = gate_daily_loss(
        _order("buy"),
        start_equity=Decimal("1000000"),
        equity=Decimal("980000"),
    )
    assert gated.status == STATUS_NEW


def test_daily_loss_over_limit_blocks_entry_not_exit() -> None:
    start = Decimal("1000000")
    now = Decimal("960000")
    denied = gate_daily_loss(_order("buy"), start_equity=start, equity=now)
    assert denied.status == STATUS_REJECTED
    assert denied.raw["reject_reason"] == DAILY_LOSS_EXCEEDED

    exit_order = gate_daily_loss(_order("sell"), start_equity=start, equity=now)
    assert exit_order.status == STATUS_NEW
