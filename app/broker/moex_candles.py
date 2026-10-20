"""Публичные свечи MOEX ISS для paper-бэктеста и worker CSV."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
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
    with urlopen(url, timeout=90) as response:  # noqa: S310
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


def fetch_moex_candles_chunked(
    ticker: str,
    *,
    from_day: date,
    till_day: date,
    interval: int = 1,
    chunk_days: int = 14,
    request_json: Callable[[str], dict] = _request_json,
) -> list[CandleBar]:
    """Тянем историю короткими окнами и склеиваем (для 1m→15m за длинный срок)."""
    if chunk_days < 1:
        raise ValueError("chunk_days")
    if till_day < from_day:
        return []
    merged: list[CandleBar] = []
    seen: set[datetime] = set()
    cursor = from_day
    total_days = max((till_day - from_day).days + 1, 1)
    while cursor <= till_day:
        window_end = min(cursor + timedelta(days=chunk_days - 1), till_day)
        chunk: list[CandleBar] = []
        last_err: Exception | None = None
        for attempt in (1, 2, 3):
            try:
                chunk = fetch_moex_candles(
                    ticker,
                    from_day=cursor,
                    till_day=window_end,
                    interval=interval,
                    request_json=request_json,
                )
                last_err = None
                break
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                print(
                    f"    chunk {ticker} {cursor}..{window_end}: "
                    f"retry {attempt}/3 · {exc}",
                    flush=True,
                )
        if last_err is not None and not chunk:
            print(
                f"    chunk {ticker} {cursor}..{window_end}: SKIP окно · {last_err}",
                flush=True,
            )
        for bar in chunk:
            if bar.ts not in seen:
                seen.add(bar.ts)
                merged.append(bar)
        done_days = min((window_end - from_day).days + 1, total_days)
        print(
            f"    chunk {ticker} {cursor}..{window_end}: "
            f"+{len(chunk)} bars · total={len(merged)} · "
            f"окна {done_days}/{total_days}д",
            flush=True,
        )
        cursor = window_end + timedelta(days=1)
    return sorted(merged, key=lambda bar: bar.ts)


def aggregate_candles(
    bars: list[CandleBar],
    *,
    minutes: int,
) -> list[CandleBar]:
    if minutes < 1:
        raise ValueError("minutes")
    buckets: dict[datetime, list[CandleBar]] = {}
    for bar in sorted(bars, key=lambda item: item.ts):
        timestamp = bar.ts.astimezone(UTC)
        bucket = timestamp.replace(
            minute=(timestamp.minute // minutes) * minutes,
            second=0,
            microsecond=0,
        )
        buckets.setdefault(bucket, []).append(bar)
    return [
        CandleBar(
            ts=timestamp,
            o=rows[0].o,
            h=max(row.h for row in rows),
            low=min(row.low for row in rows),
            c=rows[-1].c,
            v=sum((row.v for row in rows), Decimal("0")),
        )
        for timestamp, rows in sorted(buckets.items())
    ]


def moscow_calendar_day(raw: datetime | str) -> date | None:
    """Торговый день в Москве. 21:00 UTC — это уже полночь следующего дня."""
    if isinstance(raw, datetime):
        ts = raw
    else:
        try:
            ts = datetime.fromisoformat(str(raw))
        except ValueError:
            return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.astimezone(MOSCOW).date()


def missing_session_ranges(days: list[date], *, until: date) -> list[tuple[date, date]]:
    """Будни от первой свечи до закрытого дня, которых нет в файле. Пятница и понедельник — один отрезок."""
    if not days:
        return []
    have = set(days)
    cursor = min(days)
    end = until if until >= cursor else max(days)
    missing: list[date] = []
    while cursor <= end:
        if cursor.weekday() < 5 and cursor not in have:
            missing.append(cursor)
        cursor += timedelta(days=1)
    ranges: list[tuple[date, date]] = []
    start = prev = None
    for day in missing:
        if prev is not None and _next_weekday(prev) == day:
            prev = day
            continue
        if start is not None and prev is not None:
            ranges.append((start, prev))
        start = prev = day
    if start is not None and prev is not None:
        ranges.append((start, prev))
    return ranges


def _next_weekday(day: date) -> date:
    nxt = day + timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += timedelta(days=1)
    return nxt


def latest_closed_session(now: datetime | None = None) -> date:
    """Последний день, у которого дневная свеча уже должна быть. До 19:00 МСК это вчера."""
    local = (now or datetime.now(UTC)).astimezone(MOSCOW)
    day = local.date()
    if local.hour < 19:
        day -= timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


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
