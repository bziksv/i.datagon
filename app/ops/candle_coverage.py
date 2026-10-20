"""Покрытие CSV свечей для тестового экрана: дневки, 15м, 10м."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from pathlib import Path

from app.broker.moex_candles import (
    latest_closed_session,
    missing_session_ranges,
    moscow_calendar_day,
)
from app.ops.candle_refresh import schedule_view
from app.ops.refresh_candles import csv_tickers

# Форматы, которыми реально гоняют рукава в тесте.
STRATEGY_TFS = ("1d", "15m", "10m")

TF_META = {
    "1d": {
        "env": "CANDLE_DIR",
        "default": "data/candles",
        "min_bars": 300,
        "detail_gaps": True,
        "title": "Дневки",
        "sleeves": "Пересечение средних, Дончиан, RSI, докупы, моментум",
    },
    "15m": {
        "env": "CANDLE_M15_DIR",
        "default": "data/candles_m15",
        "min_bars": 2000,
        "detail_gaps": False,
        "title": "15 минут",
        "sleeves": "EMA-скальп",
    },
    "10m": {
        "env": "CANDLE_M10_DIR",
        "default": "data/candles_m10",
        "min_bars": 3000,
        "detail_gaps": False,
        "title": "10 минут",
        "sleeves": "Волатильный скальп",
    },
}


def candle_root(tf: str) -> Path:
    meta = TF_META[tf]
    return Path(os.environ.get(meta["env"], meta["default"]))


def coverage_view(
    *,
    tf: str,
    tickers: list[str],
    names: dict[str, str],
) -> dict:
    frame = tf.strip().lower()
    if frame not in TF_META:
        raise ValueError("unsupported tf")
    meta = TF_META[frame]
    root = candle_root(frame)
    known = set(tickers)
    for stem in csv_tickers(root):
        if stem not in known:
            tickers.append(stem)
    tickers = sorted({name.upper() for name in tickers if name})
    closed = latest_closed_session()
    session_day = closed.isoformat()
    ready = missing = short = 0
    details: list[dict] = []
    for ticker in tickers:
        name = names.get(ticker) or ticker
        path = root / f"{ticker}.csv"
        row = _file_row(
            path,
            ticker=ticker,
            name=name,
            min_bars=int(meta["min_bars"]),
            detail_gaps=bool(meta["detail_gaps"]),
            closed=closed,
        )
        if row["status"] == "ready":
            ready += 1
        elif row["status"] == "missing":
            missing += 1
        else:
            short += 1
        details.append(row)
    return {
        "tf": frame,
        "title": meta["title"],
        "sleeves": meta["sleeves"],
        "min_bars": meta["min_bars"],
        "total": len(tickers),
        "ready": ready,
        "missing": missing,
        "short": short,
        "session": session_day,
        "on_session": sum(
            1
            for row in details
            if row.get("session_day") and row["session_day"] >= session_day
        ),
        "root": str(root),
        "as_of": datetime.now(UTC).isoformat(),
        "items": details,
        "formats": [
            {
                "id": key,
                "title": value["title"],
                "sleeves": value["sleeves"],
                "min_bars": value["min_bars"],
            }
            for key, value in TF_META.items()
        ],
        "refresh": schedule_view(),
    }


def _file_row(
    path: Path,
    *,
    ticker: str,
    name: str,
    min_bars: int,
    detail_gaps: bool,
    closed: date,
) -> dict:
    if not path.exists() or path.stat().st_size < 100:
        return {
            "ticker": ticker,
            "name": name,
            "status": "missing",
            "bars": 0,
            "session_day": None,
            "gaps": [],
        }
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {
            "ticker": ticker,
            "name": name,
            "status": "missing",
            "bars": 0,
            "session_day": None,
            "gaps": [],
        }
    bars = max(0, len(lines) - 1)
    first = last = None
    if bars >= 1 and len(lines) >= 2:
        first = lines[1].split(",", 1)[0]
        last = lines[-1].split(",", 1)[0]
    session = moscow_calendar_day(last) if last else None
    gaps: list[dict] = []
    if detail_gaps and bars:
        days: list[date] = []
        for line in lines[1:]:
            parsed = moscow_calendar_day(line.split(",", 1)[0])
            if parsed is not None:
                days.append(parsed)
        if days:
            session = max(days)
            gaps = [
                {"from": start.isoformat(), "to": end.isoformat()}
                for start, end in missing_session_ranges(days, until=closed)
            ]
    elif session is not None and session < closed:
        nxt = session.toordinal() + 1
        from datetime import timedelta

        start = date.fromordinal(nxt)
        while start.weekday() >= 5:
            start += timedelta(days=1)
        if start <= closed:
            gaps = [{"from": start.isoformat(), "to": closed.isoformat()}]
    status = "short"
    if bars >= min_bars and session is not None and session >= closed:
        status = "ready"
    elif bars == 0:
        status = "missing"
    return {
        "ticker": ticker,
        "name": name,
        "status": status,
        "bars": bars,
        "first": first,
        "last": last,
        "session_day": session.isoformat() if session else None,
        "gaps": gaps,
    }
