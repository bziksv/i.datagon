from app.book.orders import STATUS_REJECTED
from app.broker.fake import FakeBroker
from app.broker.port import OrderRequest
from app.models import Flag
from app.risk.gate import place_after_gate
from app.risk.kill import KILLED
from app.risk.universe import OUTSIDE_UNIVERSE


def _req(ticker: str) -> OrderRequest:
    return OrderRequest(
        ticker=ticker,
        side="buy",
        qty=1,
        type="market",
        client_order_id=f"c-gate-{ticker}",
    )


def test_gate_deny_does_not_post_order() -> None:
    port = FakeBroker()
    order = place_after_gate(
        _req("GAZP"),
        sleeve="sma_cross",
        port=port,
        tickers=["SBER"],
    )
    assert order.status == STATUS_REJECTED
    assert order.raw["reject_reason"] == OUTSIDE_UNIVERSE
    assert order.broker_order_id is None
    assert port._orders == {}


def test_gate_allow_posts_order() -> None:
    port = FakeBroker()
    order = place_after_gate(
        _req("SBER"),
        sleeve="sma_cross",
        port=port,
        tickers=["SBER"],
    )
    assert order.broker_order_id
    assert len(port._orders) == 1


def test_gate_kill_blocks_even_in_universe() -> None:
    port = FakeBroker()
    order = place_after_gate(
        _req("SBER"),
        sleeve="sma_cross",
        port=port,
        tickers=["SBER"],
        flags=[Flag(key="kill", value=True)],
    )
    assert order.status == STATUS_REJECTED
    assert order.raw["reject_reason"] == KILLED
    assert port._orders == {}
