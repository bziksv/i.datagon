"""Все тикеры Тинькофф TQBR (fundamentals): свечи tf за N дней, пакеты по 5.

Качает только недобор (span < min-days). Лог: пакет, OK/SKIP, остаток.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models import Fundamental, Instrument
from app.ops.envfile import load_env_file
from app.ops.refresh_candles import refresh
from app.strategy.backtest import load_bars

_TF_ROOT = {
    "1m": ("CANDLE_M1_DIR", "data/candles_m1"),
    "10m": ("CANDLE_M10_DIR", "data/candles_m10"),
    "15m": ("CANDLE_M15_DIR", "data/candles_m15"),
    "60m": ("CANDLE_H1_DIR", "data/candles_h1"),
    "1d": ("CANDLE_DIR", "data/candles"),
}


async def _tickers_from_db() -> list[str]:
    Session = get_sessionmaker()
    async with Session() as session:
        fund = (
            await session.execute(select(Fundamental.ticker).order_by(Fundamental.ticker))
        ).scalars().all()
        if fund:
            return [str(t).upper() for t in fund if t]
        rows = (
            await session.execute(
                select(Instrument.ticker)
                .where(Instrument.class_code == "TQBR")
                .order_by(Instrument.ticker)
            )
        ).scalars().all()
        return [str(t).upper() for t in rows if t]


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
    parser.add_argument("--tf", choices=sorted(_TF_ROOT), required=True)
    parser.add_argument("--days", type=int, default=730)
    parser.add_argument("--batch", type=int, default=5)
    parser.add_argument("--min-days", type=int, default=600)
    parser.add_argument("--root")
    args = parser.parse_args()
    if args.batch < 1:
        raise SystemExit("--batch must be >= 1")

    load_env_file(Path(".env"))
    env_key, default_root = _TF_ROOT[args.tf]
    root = Path(args.root or os.environ.get(env_key, default_root))
    root.mkdir(parents=True, exist_ok=True)

    tickers = asyncio.run(_tickers_from_db())
    if not tickers:
        raise SystemExit("нет тикеров в fundamentals/instruments")
    # кэш для чеклиста без повторного asyncio в том же процессе
    cache = Path("data/logs/tqbr_tickers.txt")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("\n".join(tickers) + "\n", encoding="utf-8")

    pending = [t for t in tickers if _days(root / f"{t}.csv") < args.min_days]
    todo = len(pending)
    print(
        f"старт {datetime.now(UTC).isoformat()} · tf={args.tf} · вселенная {len(tickers)} · "
        f"к загрузке {todo} · пакет {args.batch} · дней {args.days} · min_days {args.min_days} · {root}"
    )
    done = ok = skip = 0
    for index in range(0, todo, args.batch):
        chunk = pending[index : index + args.batch]
        left_companies = todo - done
        print(
            f"\nпакет {index // args.batch + 1} · компании: {', '.join(chunk)} · "
            f"осталось компаний по {args.tf}: {left_companies}"
        )
        for ticker in chunk:
            try:
                path = refresh([ticker], days=args.days, tf=args.tf, root=root)[0]
                bars = sum(1 for _ in path.open(encoding="utf-8")) - 1
                span = _days(path)
                print(f"  OK {ticker}: bars={bars} span_days={span}")
                ok += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  SKIP {ticker}: {exc}")
                skip += 1
            done += 1
            print(
                f"  прогресс {done}/{todo} · осталось компаний по {args.tf}: "
                f"{todo - done}"
            )
        # после пакета из 5 — обновляем матрицу компания→свечи
        try:
            from app.ops.candles_2y_checklist_write import write_company_checklist

            write_company_checklist()
            print(
                f"  чеклист обновлён · осталось компаний по {args.tf}: "
                f"{todo - done}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  WARN checklist: {exc}")
    print(
        f"\nготово · tf={args.tf} · ok={ok} skip={skip} · "
        f"файлов {len(list(root.glob('*.csv')))} · "
        f"осталось компаний по {args.tf}: 0"
    )


if __name__ == "__main__":
    main()
