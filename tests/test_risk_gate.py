from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from app.book.orders import STATUS_REJECTED
from app.broker.fake import FakeBroker
from app.broker.port import OrderRequest
from app.models import Flag
from app.risk.context import RISK_CONTEXT_MISSING, RiskContext
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


def _context() -> RiskContext:
    return RiskContext(
        price=Decimal("100"),
        price_as_of=datetime.now(UTC),
        equity=Decimal("1000000"),
        start_equity=Decimal("1000000"),
        stop_price=Decimal("90"),
    )


def test_gate_deny_does_not_post_order() -> None:
    port = FakeBroker()
    order = place_after_gate(
        _req("GAZP"),
        sleeve="sma_cross",
        port=port,
        tickers=["SBER"],
        context=_context(),
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
        context=_context(),
    )
    assert order.broker_order_id
    assert len(port._orders) == 1
    assert order.raw["risk_policy_version"] == "risk-v1"
    assert order.raw["risk_context"]["price"] == 100.0
    assert [row["code"] for row in order.raw["risk_checks"]] == [
        "universe",
        "kill_switch",
        "once_per_bar",
        "earnings",
        "risk_context",
        "trade_risk",
        "portfolio",
        "name_concentration",
        "sleeve_exposure",
        "daily_loss",
        "broker_submit",
    ]


def test_gate_kill_blocks_even_in_universe() -> None:
    port = FakeBroker()
    order = place_after_gate(
        _req("SBER"),
        sleeve="sma_cross",
        port=port,
        tickers=["SBER"],
        flags=[Flag(key="kill", value=True)],
        context=_context(),
    )
    assert order.status == STATUS_REJECTED
    assert order.raw["reject_reason"] == KILLED
    assert port._orders == {}


def test_gate_fails_closed_without_complete_risk_context() -> None:
    port = FakeBroker()
    order = place_after_gate(
        _req("SBER"),
        sleeve="sma_cross",
        port=port,
        tickers=["SBER"],
    )
    assert order.status == STATUS_REJECTED
    assert order.raw["reject_reason"] == RISK_CONTEXT_MISSING
    assert port._orders == {}


def test_gate_limits_quantity_by_entry_stop_risk() -> None:
    port = FakeBroker()
    order = place_after_gate(
        OrderRequest(
            ticker="SBER",
            side="buy",
            qty=600,
            type="market",
            client_order_id="risk-sized",
        ),
        sleeve="sma_cross",
        port=port,
        tickers=["SBER"],
        context=_context(),
    )
    assert order.status == STATUS_REJECTED
    assert order.raw["reject_reason"] == "trade_risk_limit"
    assert port._orders == {}


def test_gate_blocks_risk_increase_when_broker_state_is_unknown() -> None:
    base = _context()
    context = RiskContext(
        price=base.price,
        price_as_of=base.price_as_of,
        equity=base.equity,
        start_equity=base.start_equity,
        stop_price=base.stop_price,
        broker_healthy=False,
    )
    port = FakeBroker()
    order = place_after_gate(
        _req("SBER"),
        sleeve="sma_cross",
        port=port,
        tickers=["SBER"],
        context=context,
    )
    assert order.status == STATUS_REJECTED
    assert order.raw["reject_reason"] == "risk_broker_unknown"
    assert port._orders == {}


def test_gate_blocks_portfolio_gross_exposure() -> None:
    port = FakeBroker()
    order = place_after_gate(
        _req("SBER"),
        sleeve="sma_cross",
        port=port,
        tickers=["SBER"],
        context=replace(_context(), gross_existing=Decimal("999950")),
    )
    assert order.status == STATUS_REJECTED
    assert order.raw["reject_reason"] == "gross_exposure"
    assert port._orders == {}
