from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.book.accounts import TRADING_CASH
from app.book.valuation import PriceMark, value_portfolio
from app.models import EquitySnapshot, LedgerEntry, Position


def _entry(amount: str) -> LedgerEntry:
    return LedgerEntry(
        account_kind=TRADING_CASH,
        amount=Decimal(amount),
        reason="deposit",
        ts=datetime(2026, 10, 12, 9, 0, tzinfo=UTC),
    )


def _position(instrument_id) -> Position:
    return Position(
        id=uuid4(),
        sleeve="sma_cross",
        instrument_id=instrument_id,
        qty=10,
        avg_price=Decimal("100"),
    )


def test_market_mark_drives_equity_and_unrealized_pnl() -> None:
    instrument_id = uuid4()
    now = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
    result = value_portfolio(
        [_entry("5000")],
        [_position(instrument_id)],
        {
            instrument_id: PriceMark(
                instrument_id,
                Decimal("110"),
                now - timedelta(minutes=1),
                "candle:1d",
            )
        },
        now=now,
    )
    assert result["status"] == "complete"
    assert result["equity"] == 6100.0
    assert result["unrealized_pnl"] == 100.0
    assert result["positions"][0]["cost_basis"] == 1000.0
    assert result["positions"][0]["market_value"] == 1100.0


def test_missing_or_stale_mark_never_masquerades_as_exact_equity() -> None:
    instrument_id = uuid4()
    now = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
    missing = value_portfolio(
        [_entry("5000")],
        [_position(instrument_id)],
        {},
        now=now,
    )
    stale = value_portfolio(
        [_entry("5000")],
        [_position(instrument_id)],
        {
            instrument_id: PriceMark(
                instrument_id,
                Decimal("110"),
                now - timedelta(days=3),
                "candle:1d",
            )
        },
        now=now,
    )
    assert missing["status"] == "partial"
    assert missing["equity"] is None
    assert missing["data_quality"]["missing_marks"] == 1
    assert stale["status"] == "partial"
    assert stale["equity"] is None
    assert stale["positions"][0]["mark_quality"] == "stale"


def test_peak_drawdown_and_day_start_are_reproducible_from_snapshots() -> None:
    now = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
    snapshots = [
        EquitySnapshot(
            ts=now - timedelta(hours=3),
            trading_cash=1000,
            vault=0,
            positions_value=0,
            equity=1000,
        ),
        EquitySnapshot(
            ts=now - timedelta(hours=1),
            trading_cash=800,
            vault=0,
            positions_value=0,
            equity=800,
        ),
    ]
    result = value_portfolio(
        [_entry("800")],
        [],
        {},
        snapshots=snapshots,
        now=now,
    )
    assert result["peak_equity"] == 1000.0
    assert result["day_start_equity"] == 1000.0
    assert result["max_drawdown"] == 0.2
