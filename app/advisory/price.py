"""Рыночная цена для paper-плана: БД candles, иначе последний бар CSV."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from app.strategy.backtest import load_bars


def candle_dir() -> Path:
    return Path(os.environ.get("CANDLE_DIR", "data/candles"))


def last_csv_mark(
    ticker: str,
    *,
    root: Path | None = None,
) -> tuple[Decimal, datetime] | None:
    path = (root or candle_dir()) / f"{ticker.strip().upper()}.csv"
    if not path.is_file() or path.stat().st_size <= 0:
        return None
    try:
        bars = load_bars(path)
    except (OSError, ValueError):
        return None
    if not bars:
        return None
    bar = bars[-1]
    ts = bar.ts if bar.ts.tzinfo is not None else bar.ts.replace(tzinfo=UTC)
    close = Decimal(str(bar.c))
    if close <= 0:
        return None
    return close, ts


def resolve_mark_price(
    *,
    ticker: str,
    instrument_id: UUID | None,
    latest_by_instrument: dict[UUID, object],
) -> tuple[Decimal, datetime] | None:
    if instrument_id is not None:
        candle = latest_by_instrument.get(instrument_id)
        if candle is not None:
            raw_ts = getattr(candle, "ts")
            ts = (
                raw_ts
                if raw_ts.tzinfo is not None
                else raw_ts.replace(tzinfo=UTC)
            )
            close = Decimal(str(getattr(candle, "c")))
            if close > 0:
                return close, ts
    return last_csv_mark(ticker)
