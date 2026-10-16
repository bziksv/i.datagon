"""CLI: обновить CSV свечей из публичного MOEX ISS."""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.broker.moex_candles import (
    aggregate_candles,
    fetch_moex_candles,
    fetch_moex_candles_chunked,
    write_candle_csv,
)
from app.ops.envfile import load_env_file


def csv_tickers(root: Path) -> list[str]:
    """Имена уже лежащих дневных CSV. Широта смотрит весь каталог, не один тикер."""
    if not root.is_dir():
        return []
    return sorted({path.stem.upper() for path in root.glob("*.csv") if path.stem})


def refresh(
    tickers: list[str],
    *,
    days: int,
    tf: str,
    root: Path,
) -> list[Path]:
    if days < 1:
        raise ValueError("days")
    if tf == "1d":
        interval = 24
    elif tf == "10m":
        interval = 10
    elif tf == "60m":
        interval = 60
    elif tf in {"1m", "15m"}:
        interval = 1
    else:
        raise ValueError("tf")
    today = datetime.now(UTC).date()
    from_day = today - timedelta(days=days)
    written = []
    for ticker in tickers:
        symbol = ticker.strip().upper()
        if tf in {"1m", "15m"}:
            # ISS режет длинный 1m — тянем окнами по 14 дней и склеиваем
            bars = fetch_moex_candles_chunked(
                symbol,
                from_day=from_day,
                till_day=today,
                interval=1,
                chunk_days=14,
            )
            if tf == "15m":
                bars = aggregate_candles(bars, minutes=15)
        else:
            bars = fetch_moex_candles(
                symbol,
                from_day=from_day,
                till_day=today,
                interval=interval,
            )
        written.append(write_candle_csv(root / f"{symbol}.csv", bars))
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh paper candle CSV from MOEX")
    parser.add_argument("--ticker", action="append", default=[])
    parser.add_argument(
        "--desk-all",
        action="store_true",
        help="все тикеры из отраслевых групп desk (ядро + нефть, банки, …)",
    )
    parser.add_argument("--days", type=int, default=730)
    parser.add_argument(
        "--tf", choices=("1m", "10m", "15m", "60m", "1d"), default="1d"
    )
    parser.add_argument("--root")
    args = parser.parse_args()

    load_env_file(Path(".env"))
    roots = {
        "1m": os.environ.get("CANDLE_M1_DIR", "data/candles_m1"),
        "10m": os.environ.get("CANDLE_M10_DIR", "data/candles_m10"),
        "15m": os.environ.get("CANDLE_M15_DIR", "data/candles_m15"),
        "60m": os.environ.get("CANDLE_H1_DIR", "data/candles_h1"),
        "1d": os.environ.get("CANDLE_DIR", "data/candles"),
    }
    default_root = roots[args.tf]
    root = Path(args.root or default_root)
    tickers = [name.strip().upper() for name in args.ticker if name.strip()]
    if args.desk_all:
        from app.strategy.moex_groups import all_moex_desk_tickers

        for name in all_moex_desk_tickers():
            if name not in tickers:
                tickers.append(name)
    if not tickers:
        raise SystemExit("укажите --ticker и/или --desk-all")
    for ticker in tickers:
        try:
            path = refresh([ticker], days=args.days, tf=args.tf, root=root)[0]
            print(path)
        except Exception as exc:  # noqa: BLE001 — fail-soft по имени
            print(f"SKIP {ticker}: {exc}")


if __name__ == "__main__":
    main()
