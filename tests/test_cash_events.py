from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.book.events import cash_event, cash_event_summary


def test_cash_events_keep_costs_taxes_and_dividends_separate() -> None:
    now = datetime(2026, 10, 12, tzinfo=UTC)
    rows = [
        cash_event("commission", Decimal("10"), ts=now),
        cash_event("fee", Decimal("2.50"), ts=now),
        cash_event("tax", Decimal("13"), ts=now),
        cash_event("dividend", Decimal("100"), ts=now),
        cash_event("deposit", Decimal("1000"), ts=now),
        cash_event("withdrawal", Decimal("50"), ts=now),
    ]
    assert [Decimal(str(row.amount)) for row in rows] == [
        Decimal("-10"),
        Decimal("-2.50"),
        Decimal("-13"),
        Decimal("100"),
        Decimal("1000"),
        Decimal("-50"),
    ]
    assert cash_event_summary(rows) == {
        "commission": -10.0,
        "deposit": 1000.0,
        "dividend": 100.0,
        "fee": -2.5,
        "tax": -13.0,
        "withdrawal": -50.0,
    }


def test_unknown_cash_event_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported cash event"):
        cash_event("magic_profit", Decimal("100"))
