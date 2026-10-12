"""Недельный paper-отчёт: считаем по equity_snapshots."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.book.valuation import VALUATION_VERSION
from app.models import EquitySnapshot, Report

WEEKLY_PAPER = "weekly_paper"


def week_bounds(ts: datetime) -> tuple[datetime, datetime]:
    day = ts.astimezone(UTC).date()
    monday = day - timedelta(days=day.weekday())
    start = datetime(monday.year, monday.month, monday.day, tzinfo=UTC)
    return start, start + timedelta(days=7)


def snapshots_in_week(
    rows: Sequence[EquitySnapshot],
    start: datetime,
    end: datetime,
) -> list[EquitySnapshot]:
    return sorted(
        (row for row in rows if start <= row.ts < end),
        key=lambda row: row.ts,
    )


def weekly_paper_report(
    snapshots: Sequence[EquitySnapshot],
    *,
    ts: datetime,
) -> Report | None:
    start, end = week_bounds(ts)
    week = snapshots_in_week(snapshots, start, end)
    if not week:
        return None
    first, last = week[0], week[-1]
    equity_start = Decimal(str(first.equity))
    equity_end = Decimal(str(last.equity))
    return Report(
        kind=WEEKLY_PAPER,
        period_start=start,
        period_end=end,
        equity_start=equity_start,
        equity_end=equity_end,
        pnl=equity_end - equity_start,
        payload={
            "snapshots": len(week),
            "valuation_version": VALUATION_VERSION,
        },
    )


def merge_report(existing: Report | None, incoming: Report) -> Report:
    if existing is None:
        return incoming
    existing.period_end = incoming.period_end
    existing.equity_start = incoming.equity_start
    existing.equity_end = incoming.equity_end
    existing.pnl = incoming.pnl
    existing.payload = incoming.payload
    return existing


def apply_weekly_report(
    existing: Sequence[Report],
    snapshots: Sequence[EquitySnapshot],
    *,
    ts: datetime,
) -> list[Report]:
    incoming = weekly_paper_report(snapshots, ts=ts)
    if incoming is None:
        return list(existing)
    rows = list(existing)
    found = next(
        (
            row
            for row in rows
            if row.kind == incoming.kind and row.period_start == incoming.period_start
        ),
        None,
    )
    merged = merge_report(found, incoming)
    if found is None:
        rows.append(merged)
    return rows
