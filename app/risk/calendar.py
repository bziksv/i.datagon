"""Календарь отчётов: таблица, ручное наполнение на старте."""

from collections.abc import Sequence
from datetime import date
from uuid import uuid4

from app.models import EarningsDay

SEED_EARNINGS: tuple[tuple[str, date], ...] = (
    ("SBER", date(2026, 11, 12)),
    ("GAZP", date(2026, 11, 19)),
    ("LKOH", date(2026, 11, 26)),
)


def seed_earnings(existing: Sequence[EarningsDay] = ()) -> list[EarningsDay]:
    seen = {(row.ticker.upper(), row.day) for row in existing}
    rows = list(existing)
    for ticker, day in SEED_EARNINGS:
        key = (ticker.upper(), day)
        if key in seen:
            continue
        rows.append(EarningsDay(id=uuid4(), ticker=ticker, day=day))
        seen.add(key)
    return rows


def calendar_map(rows: Sequence[EarningsDay]) -> dict[str, list[date]]:
    out: dict[str, list[date]] = {}
    for row in rows:
        out.setdefault(row.ticker.upper(), []).append(row.day)
    return out
