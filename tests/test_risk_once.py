from app.book.orders import STATUS_NEW, STATUS_REJECTED, draft_order
from app.broker.port import OrderRequest
from app.models import Order
from app.risk.once import ALREADY_ENTERED, gate_once_per_bar


def _order(ticker: str, side: str = "buy") -> Order:
    return draft_order(
        OrderRequest(
            ticker=ticker,
            side=side,
            qty=1,
            type="market",
            client_order_id=f"c-once-{ticker}-{side}",
        ),
        sleeve="sma_cross",
    )


def test_one_entry_per_ticker_per_bar() -> None:
    first = gate_once_per_bar(_order("SBER"), [])
    assert first.status == STATUS_NEW

    second = gate_once_per_bar(_order("SBER"), ["SBER"])
    assert second.status == STATUS_REJECTED
    assert second.raw["reject_reason"] == ALREADY_ENTERED

    other = gate_once_per_bar(_order("GAZP"), ["SBER"])
    assert other.status == STATUS_NEW

    exit_order = gate_once_per_bar(_order("SBER", "sell"), ["SBER"])
    assert exit_order.status == STATUS_NEW
