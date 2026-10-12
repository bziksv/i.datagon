from datetime import date

from app.book.orders import STATUS_NEW, STATUS_REJECTED, draft_order
from app.broker.port import OrderRequest
from app.risk.earnings import EARNINGS_DAY, gate_earnings


def _order(ticker: str, side: str = "buy") -> object:
    return draft_order(
        OrderRequest(
            ticker=ticker,
            side=side,
            qty=1,
            type="market",
            client_order_id=f"c-earn-{ticker}-{side}",
        ),
        sleeve="sma_cross",
    )


def test_earnings_day_blocks_entry() -> None:
    day = date(2026, 10, 12)
    calendar = {"SBER": [day]}
    blocked = gate_earnings(_order("SBER"), calendar, day)
    assert blocked.status == STATUS_REJECTED
    assert blocked.raw["reject_reason"] == EARNINGS_DAY

    other = gate_earnings(_order("GAZP"), calendar, day)
    assert other.status == STATUS_NEW

    later = gate_earnings(_order("SBER"), calendar, date(2026, 10, 13))
    assert later.status == STATUS_NEW

    exit_order = gate_earnings(_order("SBER", "sell"), calendar, day)
    assert exit_order.status == STATUS_NEW
