"""Матрица: компания → 1m / 10m / 15m / 60m / 1d."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models import Fundamental
from app.ops.envfile import load_env_file

ROOTS = {
    "1m": (Path("data/candles_m1"), 150),
    "10m": (Path("data/candles_m10"), 600),
    "15m": (Path("data/candles_m15"), 150),
    "60m": (Path("data/candles_h1"), 600),
    "1d": (Path("data/candles"), 600),
}
OUT = Path("data/logs/CANDLES_2Y_CHECKLIST.md")
TICKERS_CACHE = Path("data/logs/tqbr_tickers.txt")


async def _tickers_db() -> list[str]:
    Session = get_sessionmaker()
    async with Session() as session:
        rows = (
            await session.execute(select(Fundamental.ticker).order_by(Fundamental.ticker))
        ).scalars().all()
        return [str(t).upper() for t in rows if t]


def load_tickers() -> list[str]:
    """Без повторного asyncio.run в том же процессе — кэш-файл."""
    if TICKERS_CACHE.exists():
        names = [
            line.strip().upper()
            for line in TICKERS_CACHE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if names:
            return names
    load_env_file(Path(".env"))
    loop = asyncio.new_event_loop()
    try:
        names = loop.run_until_complete(_tickers_db())
    finally:
        loop.close()
    TICKERS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TICKERS_CACHE.write_text("\n".join(names) + "\n", encoding="utf-8")
    return names


def _span_days(path: Path) -> int | None:
    """Быстро: первая/последняя строка CSV, без полной загрузки."""
    if not path.exists() or path.stat().st_size < 100:
        return None
    try:
        with path.open(encoding="utf-8") as handle:
            header = handle.readline()
            first = handle.readline()
            if not first:
                return 0
            last = first
            for line in handle:
                if line.strip():
                    last = line
        start = first.split(",", 1)[0].strip()
        end = last.split(",", 1)[0].strip()
        t0 = datetime.fromisoformat(start)
        t1 = datetime.fromisoformat(end)
        return max(0, (t1 - t0).days)
    except Exception:  # noqa: BLE001
        return None


def _mark(days: int | None, need: int) -> str:
    if days is None:
        return "❌"
    if days >= need:
        return f"✅{days}d"
    return f"⚠️{days}d"


def write_company_checklist(path: Path = OUT) -> Path:
    load_env_file(Path(".env"))
    tickers = load_tickers()
    need_left = {tf: 0 for tf in ROOTS}
    lines = [
        "# Чеклист: компания → свечи",
        "",
        "Вселенная: Тинькофф TQBR (`fundamentals`). Пакеты **по 5 компаний**.",
        "",
        "Пороги: **10m/60m/1d ≥600д (~2г)** · **1m/15m ≥150д** (тянем кусками).",
        "",
        "Легенда: ✅ порог ок · ⚠️ есть, но мало · ❌ нет файла",
        "",
        "| # | Тикер | 1m | 10m | 15m | 60m | 1d |",
        "|---|---|---|---|---|---|---|",
    ]
    for index, ticker in enumerate(tickers, 1):
        cells = []
        for tf, (root, need) in ROOTS.items():
            days = _span_days(root / f"{ticker}.csv")
            if days is None or days < need:
                need_left[tf] += 1
            cells.append(_mark(days, need))
        lines.append(f"| {index} | {ticker} | " + " | ".join(cells) + " |")
    lines.extend(
        [
            "",
            "## Осталось компаний",
            f"- **1m (≥150д):** {need_left['1m']}",
            f"- **10m (≥600д):** {need_left['10m']}",
            f"- **15m (≥150д):** {need_left['15m']}",
            f"- **60m (≥600д):** {need_left['60m']}",
            f"- **1d (≥600д):** {need_left['1d']}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    print(write_company_checklist())


if __name__ == "__main__":
    main()
