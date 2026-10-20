"""Дневки теста: скачать с песочницы брокера в CSV. Заявок нет."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.broker.moex_candles import write_candle_csv
from app.broker.tinkoff import fetch_candles, find_moex_instrument


def pull_daily(ticker: str, *, days: int = 730, root: Path | None = None) -> int:
    symbol = ticker.strip().upper()
    if not symbol or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for ch in symbol):
        raise ValueError("нужен тикер латиницей")
    if days < 1 or days > 800:
        raise ValueError("дней от 1 до 800")
    instrument = find_moex_instrument(symbol)
    figi = getattr(instrument, "figi", "") or ""
    if not figi:
        raise ValueError("у бумаги нет figi")
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    bars = []
    seen = set()
    cursor = start
    while cursor < end:
        nxt = min(cursor + timedelta(days=90), end)
        chunk = fetch_candles(figi=figi, tf="1d", from_=cursor, to=nxt, limit=240)
        for bar in chunk:
            key = bar.ts.date().isoformat()
            if key in seen:
                continue
            seen.add(key)
            bars.append(bar)
        cursor = nxt
    if not bars:
        raise ValueError("брокер не отдал дневки")
    dest = (root or Path(os.environ.get("CANDLE_DIR", "data/candles"))) / f"{symbol}.csv"
    write_candle_csv(dest, bars)
    return len(bars)
