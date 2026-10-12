from datetime import UTC, datetime
from decimal import Decimal

from app.book.equity import make_snapshot
from app.book.reports import WEEKLY_PAPER, apply_weekly_report, weekly_paper_report


def _snap(day: int, equity: str, hour: int = 10) -> object:
    cash = Decimal(equity)
    return make_snapshot(
        trading_cash=cash,
        ts=datetime(2026, 10, day, hour, 0, tzinfo=UTC),
    )


def test_weekly_report_from_snapshots() -> None:
    # 2026-10-12 — понедельник
    snaps = [_snap(12, "1000000"), _snap(14, "1010000"), _snap(19, "1100000")]
    row = weekly_paper_report(snaps, ts=datetime(2026, 10, 15, tzinfo=UTC))
    assert row is not None
    assert row.kind == WEEKLY_PAPER
    assert row.period_start == datetime(2026, 10, 12, tzinfo=UTC)
    assert row.period_end == datetime(2026, 10, 19, tzinfo=UTC)
    assert Decimal(str(row.equity_start)) == Decimal("1000000")
    assert Decimal(str(row.equity_end)) == Decimal("1010000")
    assert Decimal(str(row.pnl)) == Decimal("10000")
    assert row.payload["snapshots"] == 2


def test_empty_week_has_no_report() -> None:
    assert weekly_paper_report([], ts=datetime(2026, 10, 15, tzinfo=UTC)) is None


def test_repeat_week_updates_same_row() -> None:
    first = apply_weekly_report(
        [],
        [_snap(12, "1000000")],
        ts=datetime(2026, 10, 13, tzinfo=UTC),
    )
    later = apply_weekly_report(
        first,
        [_snap(12, "1000000"), _snap(14, "1005000")],
        ts=datetime(2026, 10, 15, tzinfo=UTC),
    )
    assert len(later) == 1
    assert later[0] is first[0]
    assert Decimal(str(later[0].pnl)) == Decimal("5000")
