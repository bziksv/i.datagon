"""Расписание автообновления фундаментала воркером — для экрана Компании."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_STAMP = "data/logs/fundamentals-refresh.beat"


def stamp_path() -> Path:
    return Path(os.environ.get("FUNDAMENTALS_REFRESH_BEAT_PATH", DEFAULT_STAMP))


def interval_sec() -> int:
    try:
        return max(0, int(os.environ.get("FUNDAMENTALS_INTERVAL_SEC", "3600")))
    except ValueError:
        return 3600


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
    now = (now or datetime.now(UTC)).astimezone(UTC)
    seconds = interval_sec()
    last = read_stamp()
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
    }
