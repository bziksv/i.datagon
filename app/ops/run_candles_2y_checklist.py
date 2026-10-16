"""Строго по data/logs/CANDLES_2Y_CHECKLIST.md: 1d → 10m → 60m, batch=5."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(tf: str, *, days: int, min_days: int) -> int:
    cmd = [
        sys.executable,
        "-u",
        "-m",
        "app.ops.refresh_candles_universe_tf",
        "--tf",
        tf,
        "--days",
        str(days),
        "--batch",
        "5",
        "--min-days",
        str(min_days),
    ]
    print(
        f"\n######## CHECKLIST · {tf} · days={days} min_days={min_days} ########",
        flush=True,
    )
    return subprocess.call(cmd)


def main() -> None:
    checklist = Path("data/logs/CANDLES_2Y_CHECKLIST.md")
    print(f"чеклист: {checklist.resolve()}", flush=True)
    # порядок как в чеклисте: 1m → 10m → 15m → 60m → 1d
    plan = (
        ("1m", 730, 150),  # кусками
        ("10m", 730, 600),
        ("15m", 730, 150),  # кусками из 1m
        ("60m", 730, 600),
        ("1d", 730, 600),
    )
    for tf, days, min_days in plan:
        for attempt in (1, 2, 3):
            print(f"\n=== {tf} попытка {attempt}/3 ===", flush=True)
            code = _run(tf, days=days, min_days=min_days)
            if code != 0:
                print(f"WARN {tf} exit={code}", flush=True)
    print("\n######## CHECKLIST · прогоны закончены · сверка ########", flush=True)
    subprocess.call([sys.executable, "-u", "-m", "app.ops.candles_2y_checklist_write"])
    subprocess.call([sys.executable, "-u", "-m", "app.ops.candles_2y_report"])


if __name__ == "__main__":
    main()
