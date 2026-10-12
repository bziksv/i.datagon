from app.book.orders import STATUS_NEW, STATUS_REJECTED, draft_order
from app.broker.port import OrderRequest
from app.risk.universe import OUTSIDE_UNIVERSE, gate_universe


def _req(ticker: str) -> OrderRequest:
    return OrderRequest(
        ticker=ticker,
        side="buy",
        qty=1,
        type="market",
        client_order_id=f"c-{ticker}",
    )


def test_ticker_outside_sieve_is_rejected() -> None:
    order = draft_order(_req("GAZP"), sleeve="manual")
    gated = gate_universe(order, ["SBER"])
    assert gated.status == STATUS_REJECTED
    assert gated.raw["reject_reason"] == OUTSIDE_UNIVERSE


def test_ticker_in_sieve_passes() -> None:
    order = draft_order(_req("sber"), sleeve="manual")
    gated = gate_universe(order, ["SBER", "GAZP"])
    assert gated.status == STATUS_NEW
    assert gated.raw.get("reject_reason") is None
