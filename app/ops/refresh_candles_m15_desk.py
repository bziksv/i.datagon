"""M15 за N дней по desk-тикерам, пакеты по 5, с остатком."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from app.ops.envfile import load_env_file
from app.ops.refresh_candles import refresh
from app.strategy.backtest import load_bars
from app.strategy.moex_groups import all_moex_desk_tickers


def _days(path: Path) -> int:
    if not path.exists() or path.stat().st_size < 1000:
        return 0
    try:
        bars = load_bars(path)
    except Exception:  # noqa: BLE001
        return 0
    if not bars:
        return 0
    return (bars[-1].ts - bars[0].ts).days


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--batch", type=int, default=5)
    parser.add_argument("--min-days", type=int, default=150)
    parser.add_argument("--root", default="data/candles_m15")
    args = parser.parse_args()

    load_env_file(Path(".env"))
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    tickers = list(all_moex_desk_tickers())
    pending = [t for t in tickers if _days(root / f"{t}.csv") < args.min_days]
    todo = len(pending)
    print(
        f"старт {datetime.now(UTC).isoformat()} · desk {len(tickers)} · "
        f"к загрузке M15 {todo} · пакет {args.batch} · дней {args.days}"
    )
    done = ok = skip = 0
    for index in range(0, todo, args.batch):
        chunk = pending[index : index + args.batch]
        print(
            f"\nпакет {index // args.batch + 1}: {', '.join(chunk)} · "
            f"осталось до пакета {todo - done}"
        )
        for ticker in chunk:
            try:
                path = refresh([ticker], days=args.days, tf="15m", root=root)[0]
                bars = sum(1 for _ in path.open(encoding="utf-8")) - 1
                span = _days(path)
                print(f"  OK {ticker}: bars={bars} span_days={span}")
                ok += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  SKIP {ticker}: {exc}")
                skip += 1
            done += 1
            print(f"  прогресс {done}/{todo} · осталось {todo - done}")
    print(f"\nготово · ok={ok} skip={skip} · файлов {len(list(root.glob('*.csv')))}")


if __name__ == "__main__":
    main()
