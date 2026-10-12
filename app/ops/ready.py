"""Метрики /ready: число ордеров и last worker beat."""

import os
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_BEAT_PATH = "/var/www/i_datagon_ru_usr/data/logs/idatagon-worker.beat"
ALIVE_SEC = 3 * 3600


def beat_path() -> Path:
    return Path(os.environ.get("WORKER_BEAT_PATH", DEFAULT_BEAT_PATH))


def write_beat(ts: datetime, path: Path | None = None) -> Path:
    target = path or beat_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(ts.astimezone(UTC).isoformat(), encoding="utf-8")
    except OSError:
        return target
    return target


def read_beat(path: Path | None = None) -> datetime | None:
    target = path or beat_path()
    if not target.is_file():
        return None
    raw = target.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    return datetime.fromisoformat(raw)


def worker_alive(
    beat: datetime | None,
    now: datetime,
    *,
    window_sec: int = ALIVE_SEC,
) -> bool:
    if beat is None:
        return False
    return (now - beat).total_seconds() <= window_sec


def ready_view(
    order_count: int,
    beat: datetime | None,
    now: datetime,
    *,
    window_sec: int = ALIVE_SEC,
) -> dict:
    return {
        "status": "ok",
        "orders": order_count,
        "worker_beat": beat.isoformat() if beat else None,
        "worker_alive": worker_alive(beat, now, window_sec=window_sec),
    }
