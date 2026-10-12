"""Закрытие дневного / M15 бара → on_bar. Кабина не нужна."""

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time, timedelta
from pathlib import Path

from app.broker.port import CandleBar
from app.models import SignalRow
from app.strategy.base import BarContext, Strategy
from app.strategy.signals import record_decisions

from worker.strategy import dispatch

# TQBR: 18:50 МСК = 15:50 UTC
SESSION_CLOSE_UTC = time(15, 50)
M15_MINUTES = 15


def last_closed_day(
    now: datetime,
    close: time = SESSION_CLOSE_UTC,
) -> date:
    if now.time() >= close:
        return now.date()
    return now.date() - timedelta(days=1)


def daily_close_due(
    last_processed: date | None,
    now: datetime,
    close: time = SESSION_CLOSE_UTC,
) -> bool:
    closed = last_closed_day(now, close)
    if last_processed is None:
        return True
    return last_processed < closed


def last_closed_m15(now: datetime) -> datetime:
    """Конец последнего закрытого M15-бара (12:07 → 12:00, 11:59 → 11:45)."""
    floored = now.replace(second=0, microsecond=0)
    minute = (floored.minute // M15_MINUTES) * M15_MINUTES
    return floored.replace(minute=minute)


def m15_close_due(
    last_processed: datetime | None,
    now: datetime,
) -> bool:
    closed = last_closed_m15(now)
    if last_processed is None:
        return True
    return last_processed < closed


def on_daily_close(
    strategies: Sequence[Strategy],
    ticker: str,
    bars: Sequence[CandleBar],
    *,
    last_processed: date | None,
    now: datetime,
) -> list[SignalRow]:
    if not daily_close_due(last_processed, now):
        return []
    if not bars:
        return []
    return record_decisions(dispatch(strategies, BarContext(ticker, bars)))


def on_m15_close(
    strategies: Sequence[Strategy],
    ticker: str,
    bars: Sequence[CandleBar],
    *,
    last_processed: datetime | None,
    now: datetime,
) -> list[SignalRow]:
    if not m15_close_due(last_processed, now):
        return []
    if not bars:
        return []
    return record_decisions(dispatch(strategies, BarContext(ticker, bars)))


def close_all_books(
    strategies: Sequence[Strategy],
    books: Mapping[str, Sequence[CandleBar]],
    *,
    last_processed: date | None,
    now: datetime,
) -> list[SignalRow]:
    rows: list[SignalRow] = []
    for ticker, bars in books.items():
        if not ticker or not bars:
            continue
        rows.extend(
            on_daily_close(
                strategies,
                ticker,
                bars,
                last_processed=last_processed,
                now=now,
            )
        )
    return rows


def close_m15_books(
    strategies: Sequence[Strategy],
    books: Mapping[str, Sequence[CandleBar]],
    *,
    last_processed: datetime | None,
    now: datetime,
) -> list[SignalRow]:
    rows: list[SignalRow] = []
    for ticker, bars in books.items():
        if not ticker or not bars:
            continue
        rows.extend(
            on_m15_close(
                strategies,
                ticker,
                bars,
                last_processed=last_processed,
                now=now,
            )
        )
    return rows


def _load_books(candle_dir: str | Path | None) -> dict[str, list[CandleBar]]:
    from app.strategy.backtest import load_bars

    root = Path(candle_dir) if candle_dir else None
    if root is None or not root.is_dir():
        return {}
    books: dict[str, list[CandleBar]] = {}
    for path in sorted(root.glob("*.csv")):
        books[path.stem.upper()] = load_bars(path)
    return books


def load_daily_books(
    candle_dir: str | Path | None = None,
) -> dict[str, list[CandleBar]]:
    return _load_books(candle_dir)


def load_m15_books(
    candle_dir: str | Path | None = None,
) -> dict[str, list[CandleBar]]:
    return _load_books(candle_dir)
