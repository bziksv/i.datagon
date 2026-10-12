"""CLI: обновить CSV свечей из публичного MOEX ISS."""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.broker.moex_candles import (
    aggregate_candles,
    fetch_moex_candles,
    write_candle_csv,
)
from app.ops.envfile import load_env_file


def refresh(
    tickers: list[str],
    *,
    days: int,
    tf: str,
    root: Path,
) -> list[Path]:
    if days < 1:
        raise ValueError("days")
    interval = 24 if tf == "1d" else 1
    today = datetime.now(UTC).date()
    from_day = today - timedelta(days=days)
    written = []
    for ticker in tickers:
        symbol = ticker.strip().upper()
        bars = fetch_moex_candles(
            symbol,
            from_day=from_day,
            till_day=today,
            interval=interval,
        )
        if tf == "15m":
            bars = aggregate_candles(bars, minutes=15)
        written.append(write_candle_csv(root / f"{symbol}.csv", bars))
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh paper candle CSV from MOEX")
    parser.add_argument("--ticker", action="append", required=True)
    parser.add_argument("--days", type=int, default=730)
    parser.add_argument("--tf", choices=("1d", "15m"), default="1d")
    parser.add_argument("--root")
    args = parser.parse_args()

    load_env_file(Path(".env"))
    default_root = (
        os.environ.get("CANDLE_DIR", "data/candles")
        if args.tf == "1d"
        else os.environ.get("CANDLE_M15_DIR", "data/candles_m15")
    )
    root = Path(args.root or default_root)
    for path in refresh(args.ticker, days=args.days, tf=args.tf, root=root):
        print(path)


if __name__ == "__main__":
    main()
