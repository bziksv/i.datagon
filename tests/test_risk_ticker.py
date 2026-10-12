from uuid import uuid4

from app.book.orders import STATUS_NEW, STATUS_REJECTED, draft_order
from app.broker.port import OrderRequest
from app.models import Instrument, UniverseMember
from app.risk.universe import OUTSIDE_UNIVERSE, gate_ticker


def _instrument(ticker: str) -> Instrument:
    return Instrument(
        id=uuid4(),
        ticker=ticker,
        figi=f"FIGI-{ticker}",
        uid=f"uid-{ticker}",
        lot=10,
        currency="rub",
        class_code="TQBR",
    )


def _req(ticker: str) -> OrderRequest:
    return OrderRequest(
        ticker=ticker,
        side="buy",
        qty=1,
        type="market",
        client_order_id=f"c-risk-{ticker}",
    )


def test_ticker_must_be_in_active_universe() -> None:
    live = _instrument("SBER")
    dead = _instrument("GAZP")
    members = [
        UniverseMember(
            instrument_id=live.id, reason="tradable,rub,lot,liquid", active=True
        ),
        UniverseMember(instrument_id=dead.id, reason="not_liquid", active=False),
    ]
    instruments = [live, dead]

    ok = gate_ticker(draft_order(_req("SBER"), sleeve="sma_cross"), members, instruments)
    assert ok.status == STATUS_NEW

    denied = gate_ticker(
        draft_order(_req("GAZP"), sleeve="sma_cross"), members, instruments
    )
    assert denied.status == STATUS_REJECTED
    assert denied.raw["reject_reason"] == OUTSIDE_UNIVERSE
