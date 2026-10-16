"""Скачать дневные свечи за N дней по всем тикерам из fundamentals (Тинькофф TQBR).

Пакеты по 5; после каждого пакета пишет сколько осталось.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models import Fundamental, Instrument
from app.ops.envfile import load_env_file
from app.ops.refresh_candles import refresh


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


def _has_any_candles(path: Path) -> bool:
    """Файл уже скачан (даже если у эмитента истории меньше 2 лет)."""
    if not path.exists() or path.stat().st_size < 50:
        return False
    try:
        text = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    return len(text) >= 2


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh daily candles for all TQBR")
    parser.add_argument("--days", type=int, default=730)
    parser.add_argument("--batch", type=int, default=5)
    parser.add_argument("--root")
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="пропускать тикеры с уже достаточной историей",
    )
    args = parser.parse_args()
    if args.batch < 1:
        raise SystemExit("--batch must be >= 1")

    load_env_file(Path(".env"))
    root = Path(args.root or os.environ.get("CANDLE_DIR", "data/candles"))
    root.mkdir(parents=True, exist_ok=True)

    tickers = asyncio.run(_tickers_from_db())
    if not tickers:
        raise SystemExit("нет тикеров в fundamentals/instruments — сначала Обновить с брокера")

    if args.only_missing:
        # не долбим тикеры, у которых MOEX отдаёт короткую историю
        pending = [t for t in tickers if not _has_any_candles(root / f"{t}.csv")]
    else:
        pending = list(tickers)

    total = len(tickers)
    todo = len(pending)
    print(
        f"старт {datetime.now(UTC).isoformat()} · вселенная {total} · "
        f"к загрузке {todo} · пакет {args.batch} · дней {args.days} · {root}"
    )
    done = 0
    ok = 0
    skip = 0
    for index in range(0, todo, args.batch):
        chunk = pending[index : index + args.batch]
        remaining_before = todo - done
        print(
            f"\nпакет {index // args.batch + 1}: {', '.join(chunk)} · "
            f"осталось до пакета {remaining_before}"
        )
        for ticker in chunk:
            try:
                path = refresh([ticker], days=args.days, tf="1d", root=root)[0]
                bars = sum(1 for _ in path.open(encoding="utf-8")) - 1
                print(f"  OK {ticker}: {path} bars={bars}")
                ok += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  SKIP {ticker}: {exc}")
                skip += 1
            done += 1
            left = todo - done
            print(f"  прогресс {done}/{todo} · осталось {left}")
    print(
        f"\nготово · ok={ok} skip={skip} · файлов в {root}: "
        f"{len(list(root.glob('*.csv')))}"
    )


if __name__ == "__main__":
    main()
