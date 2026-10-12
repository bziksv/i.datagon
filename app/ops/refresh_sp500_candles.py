"""CLI: обновить CSV дневок S&P (Yahoo) для desk."""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.broker.yahoo_candles import (
    DEFAULT_SP500_DESK,
    fetch_yahoo_daily,
    write_yahoo_csv,
)
from app.ops.envfile import load_env_file


def refresh(
    tickers: list[str],
    *,
    days: int,
    root: Path,
) -> list[Path]:
    if days < 1:
        raise ValueError("days")
    today = datetime.now(UTC).date()
    from_day = today - timedelta(days=days)
    written: list[Path] = []
    for ticker in tickers:
        symbol = ticker.strip().upper()
        bars = fetch_yahoo_daily(symbol, from_day=from_day, till_day=today)
        written.append(write_yahoo_csv(root / f"{symbol}.csv", bars))
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh S&P desk candles from Yahoo")
    parser.add_argument("--ticker", action="append")
    parser.add_argument("--days", type=int, default=730)
    parser.add_argument("--root")
    args = parser.parse_args()

    load_env_file(Path(".env"))
    root = Path(args.root or os.environ.get("CANDLE_SP500_DIR", "data/candles_sp500"))
    tickers = args.ticker or list(DEFAULT_SP500_DESK)
    for path in refresh(tickers, days=args.days, root=root):
        print(path)


if __name__ == "__main__":
    main()
