"""Публичные свечи MOEX ISS для paper-бэктеста и worker CSV."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo

from app.broker.port import CandleBar

MOEX_CANDLES_URL = (
    "https://iss.moex.com/iss/engines/stock/markets/shares/"
    "boards/TQBR/securities/{ticker}/candles.json"
)
MOSCOW = ZoneInfo("Europe/Moscow")


def _request_json(url: str) -> dict:
    with urlopen(url, timeout=30) as response:  # noqa: S310
        return json.loads(response.read())


def _bar(row: dict) -> CandleBar | None:
    required = ("open", "high", "low", "close", "volume", "begin")
    if any(row.get(name) is None for name in required):
        return None
    timestamp = datetime.fromisoformat(str(row["begin"]))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=MOSCOW)
    return CandleBar(
        ts=timestamp.astimezone(UTC),
        o=Decimal(str(row["open"])),
        h=Decimal(str(row["high"])),
        low=Decimal(str(row["low"])),
        c=Decimal(str(row["close"])),
        v=Decimal(str(row["volume"])),
    )


def fetch_moex_candles(
    ticker: str,
    *,
    from_day: date,
    till_day: date,
    interval: int = 24,
    request_json: Callable[[str], dict] = _request_json,
) -> list[CandleBar]:
    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError("ticker")
    bars: list[CandleBar] = []
    seen: set[datetime] = set()
    start = 0
    while True:
        query = urlencode(
            {
                "interval": interval,
                "from": from_day.isoformat(),
                "till": till_day.isoformat(),
                "start": start,
            }
        )
        payload = request_json(
            f"{MOEX_CANDLES_URL.format(ticker=symbol)}?{query}"
        )
        block = payload.get("candles") or {}
        columns = list(block.get("columns") or [])
        data = list(block.get("data") or [])
        if not columns or not data:
            break
        added = 0
        for values in data:
            parsed = _bar(dict(zip(columns, values, strict=False)))
            if parsed is not None and parsed.ts not in seen:
                seen.add(parsed.ts)
                bars.append(parsed)
                added += 1
        if added == 0:
            break
        start += len(data)
    return sorted(bars, key=lambda bar: bar.ts)


def write_candle_csv(path: Path, bars: list[CandleBar]) -> Path:
    if not bars:
        raise ValueError("no candles")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["ts,o,h,l,c,v"]
    lines.extend(
        ",".join(
            (
                bar.ts.isoformat(),
                str(bar.o),
                str(bar.h),
                str(bar.low),
                str(bar.c),
                str(bar.v),
            )
        )
        for bar in bars
    )
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(lines) + "\n")
    temporary.replace(path)
    return path
