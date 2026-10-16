"""Сводка coverage 1d/10m/60m/15m vs fundamentals."""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models import Fundamental
from app.ops.envfile import load_env_file
from app.strategy.backtest import load_bars

ROOTS = {
    "1m": (Path("data/candles_m1"), 150),
    "10m": (Path("data/candles_m10"), 600),
    "15m": (Path("data/candles_m15"), 150),
    "60m": (Path("data/candles_h1"), 600),
    "1d": (Path("data/candles"), 600),
}


async def _tickers() -> list[str]:
    Session = get_sessionmaker()
    async with Session() as session:
        rows = (
            await session.execute(select(Fundamental.ticker).order_by(Fundamental.ticker))
        ).scalars().all()
        return [str(t).upper() for t in rows if t]


def _days(path: Path) -> int:
    if not path.exists() or path.stat().st_size < 100:
        return -1
    try:
        bars = load_bars(path)
    except Exception:  # noqa: BLE001
        return -2
    if not bars:
        return 0
    return (bars[-1].ts - bars[0].ts).days


def main() -> None:
    load_env_file(Path(".env"))
    tickers = asyncio.run(_tickers())
    print(f"вселенная fundamentals: {len(tickers)}")
    for tf, (root, need) in ROOTS.items():
        ready = short = missing = 0
        short_names: list[str] = []
        miss_names: list[str] = []
        for ticker in tickers:
            days = _days(root / f"{ticker}.csv")
            if days < 0:
                missing += 1
                if len(miss_names) < 15:
                    miss_names.append(ticker)
            elif days >= need:
                ready += 1
            else:
                short += 1
                if len(short_names) < 15:
                    short_names.append(f"{ticker}:{days}d")
        files = len(list(root.glob("*.csv"))) if root.exists() else 0
        print(
            f"{tf:4} {root}: files={files} ready>={need}d={ready} "
            f"short={short} missing={missing} · осталось={short + missing}"
        )
        if short_names:
            print(f"     short: {', '.join(short_names)}")
        if miss_names:
            print(f"     missing: {', '.join(miss_names)}")


if __name__ == "__main__":
    main()
