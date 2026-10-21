"""CLI: обновить CSV свечей из публичного MOEX ISS."""

from __future__ import annotations

import argparse
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from app.broker.moex_candles import (
    MOSCOW,
    aggregate_candles,
    fetch_moex_candles,
    fetch_moex_candles_chunked,
    write_candle_csv,
)
from app.broker.port import CandleBar
from app.ops.envfile import load_env_file
from app.strategy.backtest import load_bars

log = logging.getLogger(__name__)


def csv_tickers(root: Path) -> list[str]:
    """Имена уже лежащих дневных CSV. Широта смотрит весь каталог, не один тикер."""
    if not root.is_dir():
        return []
    return sorted({path.stem.upper() for path in root.glob("*.csv") if path.stem})


def _interval(tf: str) -> int:
    if tf == "1d":
        return 24
    if tf == "10m":
        return 10
    if tf == "60m":
        return 60
    if tf in {"1m", "15m"}:
        return 1
    raise ValueError("tf")


def _fetch(symbol: str, tf: str, from_day: date, till_day: date) -> list[CandleBar]:
    interval = _interval(tf)
    if tf in {"1m", "15m"}:
        # ISS режет длинный 1m — тянем окнами по 14 дней и склеиваем
        bars = fetch_moex_candles_chunked(
            symbol,
            from_day=from_day,
            till_day=till_day,
            interval=1,
            chunk_days=14,
        )
        if tf == "15m":
            bars = aggregate_candles(bars, minutes=15)
        return bars
    return fetch_moex_candles(
        symbol,
        from_day=from_day,
        till_day=till_day,
        interval=interval,
    )


def refresh(
    tickers: list[str],
    *,
    days: int,
    tf: str,
    root: Path,
) -> list[Path]:
    if days < 1:
        raise ValueError("days")
    _interval(tf)
    today = datetime.now(UTC).date()
    from_day = today - timedelta(days=days)
    written = []
    for ticker in tickers:
        symbol = ticker.strip().upper()
        bars = _fetch(symbol, tf, from_day, today)
        written.append(write_candle_csv(root / f"{symbol}.csv", bars))
    return written


def bar_day(bar: CandleBar) -> date:
    """Торговый день бара по Москве: дневной бар 20.10 лежит как 19.10 21:00 UTC."""
    return bar.ts.astimezone(MOSCOW).date()


def refresh_tail(
    ticker: str,
    *,
    tf: str,
    root: Path,
    depth_days: int,
    today: date | None = None,
    fetch=_fetch,
) -> Path:
    """Дотянуть хвост от последнего бара в файле и слить со старыми барами.

    Файла нет — тянем всю глубину. Последний день перекачиваем заново:
    дневной бар внутри сессии ещё растёт.
    """
    symbol = ticker.strip().upper()
    path = root / f"{symbol}.csv"
    today = today or datetime.now(MOSCOW).date()
    old = load_bars(path) if path.is_file() else []
    if old:
        lag = (today - bar_day(old[-1])).days
        days = max(1, min(depth_days, lag + 1))
    else:
        days = depth_days
    fresh = fetch(symbol, tf, today - timedelta(days=days), today)
    if not fresh and old:
        return path
    merged = {bar.ts: bar for bar in old}
    merged.update({bar.ts: bar for bar in fresh})
    return write_candle_csv(path, [merged[ts] for ts in sorted(merged)])


def refresh_tails(
    tickers: list[str],
    *,
    tf: str,
    root: Path,
    depth_days: int,
    workers: int = 4,
) -> tuple[int, int]:
    """Хвосты по всем тикерам в несколько потоков. Возвращает (ok, skip)."""
    ok = skip = 0

    def one(ticker: str) -> bool:
        error = None
        for _ in range(2):
            try:
                refresh_tail(ticker, tf=tf, root=root, depth_days=depth_days)
                return True
            except Exception as exc:  # noqa: BLE001 — fail-soft по имени
                error = exc
        log.warning("candle tail failed tf=%s ticker=%s: %s", tf, ticker, error)
        return False

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for done in pool.map(one, tickers):
            if done:
                ok += 1
            else:
                skip += 1
    return ok, skip


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
