"""Расписание автообновления свечей воркером — то, что видно на экране Свечи."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_STAMP = "data/logs/candle-refresh.beat"
DEFAULT_INTERVAL_SEC = 900


def stamp_path() -> Path:
    return Path(os.environ.get("CANDLE_REFRESH_BEAT_PATH", DEFAULT_STAMP))


def interval_sec() -> int:
    """По умолчанию раз в 15 минут (докачка хвоста). 0 в env — выключить."""
    raw = os.environ.get("CANDLE_FULL_REFRESH_INTERVAL_SEC")
    if raw is None or raw == "":
        raw = os.environ.get("CANDLE_REFRESH_INTERVAL_SEC", str(DEFAULT_INTERVAL_SEC))
    try:
        return max(0, int(raw))
    except ValueError:
        return DEFAULT_INTERVAL_SEC


def write_stamp(ts: datetime | None = None, path: Path | None = None) -> Path:
    target = path or stamp_path()
    when = (ts or datetime.now(UTC)).astimezone(UTC)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(when.isoformat(), encoding="utf-8")
    except OSError:
        return target
    return target


def read_stamp(path: Path | None = None) -> datetime | None:
    target = path or stamp_path()
    if not target.is_file():
        return None
    raw = target.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def schedule_view(now: datetime | None = None) -> dict:
    """Что пишет экран свечей: включено ли само, период, последний прогон."""
    now = (now or datetime.now(UTC)).astimezone(UTC)
    seconds = interval_sec()
    last = read_stamp()
    paper = [
        ticker.strip().upper()
        for ticker in os.environ.get("PAPER_FORWARD_TICKERS", "SBER").split(",")
        if ticker.strip()
    ]
    next_at = None
    if seconds > 0 and last is not None:
        nxt = last.timestamp() + seconds
        if nxt > now.timestamp():
            next_at = datetime.fromtimestamp(nxt, tz=UTC).isoformat()
    return {
        "enabled": seconds > 0,
        "interval_sec": seconds,
        "last_at": last.isoformat() if last else None,
        "next_at": next_at,
        "daily": "all" if seconds > 0 else "manual",
        "m15": "all" if seconds > 0 else "manual",
        "m10": "all" if seconds > 0 else "manual",
        "paper_tickers": paper,
    }
