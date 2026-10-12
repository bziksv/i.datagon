from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.book.events import cash_event
from app.book.ledger import deposit_entry
from app.book.positions import apply_fill
from app.book.reconcile import accounting_reconciliation
from app.book.valuation import PriceMark, value_portfolio
from app.models import Fill

NOW = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)


def _fill(*, qty: int, price: str, commission: str, execution_id: str) -> Fill:
    return Fill(
        id=uuid4(),
        order_id=uuid4(),
        execution_id=execution_id,
        qty=qty,
        price=Decimal(price),
        commission=Decimal(commission),
        ts=NOW,
        raw={},
    )


def test_full_trade_cycle_reconciles_to_the_cent() -> None:
    instrument_id = uuid4()
    deposit = deposit_entry([], Decimal("1000"), ts=NOW)
    assert deposit is not None
    buy = _fill(qty=1, price="100", commission="1", execution_id="buy-1")
    position, buy_cash = apply_fill(
        None,
        buy,
        sleeve="sma_cross",
        instrument_id=instrument_id,
        side="buy",
    )
    sell = _fill(qty=1, price="120", commission="1", execution_id="sell-1")
    position, sell_cash = apply_fill(
        position,
        sell,
        sleeve="sma_cross",
        instrument_id=instrument_id,
        side="sell",
    )
    valuation = value_portfolio(
        [
            deposit,
            buy_cash,
            cash_event("commission", Decimal("1"), ts=NOW),
            sell_cash,
            cash_event("commission", Decimal("1"), ts=NOW),
        ],
        [position],
        {
            instrument_id: PriceMark(
                instrument_id,
                Decimal("120"),
                NOW,
                "control",
            )
        },
        fills=[buy, sell],
        now=NOW,
    )
    report = accounting_reconciliation(valuation)
    assert valuation["equity"] == 1018.0
    assert valuation["realized_net_pnl"] == 18.0
    assert report["passed"] is True
    assert all(check["delta"] == 0.0 for check in report["checks"])


def test_partial_position_and_cash_events_reconcile() -> None:
    instrument_id = uuid4()
    deposit = deposit_entry([], Decimal("1000"), ts=NOW)
    assert deposit is not None
    buy = _fill(qty=2, price="100", commission="2", execution_id="buy-2")
    position, buy_cash = apply_fill(
        None,
        buy,
        sleeve="sma_cross",
        instrument_id=instrument_id,
        side="buy",
    )
    valuation = value_portfolio(
        [
            deposit,
            buy_cash,
            cash_event("commission", Decimal("2"), ts=NOW),
            cash_event("dividend", Decimal("5"), ts=NOW),
            cash_event("tax", Decimal("1"), ts=NOW),
        ],
        [position],
        {
            instrument_id: PriceMark(
                instrument_id,
                Decimal("110"),
                NOW,
                "control",
            )
        },
        fills=[buy],
        now=NOW,
    )
    report = accounting_reconciliation(valuation)
    assert valuation["equity"] == 1022.0
    assert valuation["unrealized_pnl"] == 18.0
    assert report["passed"] is True


def test_incomplete_or_tampered_valuation_fails_closed() -> None:
    blocked = accounting_reconciliation({"status": "partial", "equity": None})
    assert blocked["status"] == "blocked"

    mismatch = accounting_reconciliation(
        {
            "status": "complete",
            "cash": 100,
            "vault": 0,
            "known_market_value": 0,
            "positions_cost_basis": 0,
            "equity": 101,
            "unrealized_pnl": 0,
            "realized_net_pnl": 0,
            "cash_events": {"deposit": 100},
        }
    )
    assert mismatch["status"] == "failed"
    assert mismatch["passed"] is False
