from datetime import UTC, datetime
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.flat import FlatStrategy
from app.strategy.idle import IdleStrategy
from worker.bars import close_all_books, daily_close_due, last_closed_day, on_daily_close


def _bar() -> CandleBar:
    return CandleBar(
        ts=datetime(2026, 1, 9, 15, 50, tzinfo=UTC),
        o=Decimal("100"),
        h=Decimal("101"),
        low=Decimal("99"),
        c=Decimal("100.5"),
        v=Decimal("10"),
    )


def test_close_after_session_calls_on_bar() -> None:
    after = datetime(2026, 1, 9, 16, 0, tzinfo=UTC)
    assert last_closed_day(after).isoformat() == "2026-01-09"
    assert daily_close_due(None, after) is True

    rows = on_daily_close(
        [IdleStrategy(), FlatStrategy()],
        "SBER",
        [_bar()],
        last_processed=None,
        now=after,
    )
    assert len(rows) == 1
    assert rows[0].kind == "flat"
    assert rows[0].ticker == "SBER"


def test_same_closed_day_does_not_rerun() -> None:
    after = datetime(2026, 1, 9, 17, 0, tzinfo=UTC)
    assert daily_close_due(after.date(), after) is False
    assert (
        on_daily_close(
            [FlatStrategy()],
            "SBER",
            [_bar()],
            last_processed=after.date(),
            now=after,
        )
        == []
    )


def test_close_all_books_skips_empty_ticker() -> None:
    after = datetime(2026, 1, 9, 16, 0, tzinfo=UTC)
    rows = close_all_books(
        [FlatStrategy()],
        {"": [_bar()], "SBER": [_bar()]},
        last_processed=None,
        now=after,
    )
    assert len(rows) == 1
    assert rows[0].ticker == "SBER"


def test_before_session_close_is_previous_day() -> None:
    before = datetime(2026, 1, 9, 12, 0, tzinfo=UTC)
    assert last_closed_day(before).isoformat() == "2026-01-08"
