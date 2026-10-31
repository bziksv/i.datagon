"""Решение песочницы по бумаге так же, как его принимает бэктест в Тесте.

Бэктест ведёт бумагу автоматом: вне позиции стратегия смотрит вход, в позиции —
каждый бар получает цену входа и решает выход (слабые дни, трейл от пика).
Воркер считает сигналы без позиции, поэтому выход по держимым бумагам
пересчитываем здесь: прогоняем стратегию с дня входа с нашей ценой входа.
"""

from __future__ import annotations

import copy
import os
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from app.broker.port import CandleBar
from app.ops.refresh_candles import bar_day
from app.strategy.base import BarContext

DEFAULT_ROC_LOOKBACK = 15
# Позиция без истории входа (заведена руками): хватает прогрева выхода.
UNKNOWN_ENTRY_BARS = 30


def strategy_for(sleeve: str):
    from app.strategy.config import daily_strategies

    for strategy in daily_strategies(os.environ):
        if strategy.sleeve == sleeve:
            return strategy
    return None


def day_bars(ticker: str, day: date) -> list[CandleBar]:
    """Дневные бары бумаги по день решения включительно."""
    from app.strategy.backtest import load_bars

    path = Path(os.environ.get("CANDLE_DIR", "data/candles")) / f"{ticker}.csv"
    if not path.is_file():
        return []
    return [bar for bar in load_bars(path) if bar_day(bar) <= day]


def roc(
    bars: Sequence[CandleBar], lookback: int = DEFAULT_ROC_LOOKBACK
) -> Decimal | None:
    if len(bars) < lookback + 1:
        return None
    base = Decimal(bars[-(lookback + 1)].c)
    if base <= 0:
        return None
    return Decimal(bars[-1].c) / base - Decimal("1")


def held_exit(
    strategy,
    ticker: str,
    bars: Sequence[CandleBar],
    *,
    entry_price: Decimal,
    entry_day: date | None,
) -> str | None:
    """ "sell"/"exit", если стратегия в позиции закрыла бы её к последнему бару.

    Бар дня входа стратегия видела без позиции (вход по его сигналу), поэтому
    прогон с позицией начинается со следующего бара. Выход, пропущенный раньше
    (воркер лежал), тоже отдаём — продаём сейчас.
    """
    if not bars or entry_price <= 0:
        return None
    if entry_day is None:
        start = max(1, len(bars) - UNKNOWN_ENTRY_BARS)
    else:
        start = next(
            (index for index, bar in enumerate(bars) if bar_day(bar) > entry_day),
            len(bars),
        )
    replay = copy.deepcopy(strategy)
    for end in range(start, len(bars)):
        signal = replay.on_bar(
            BarContext(ticker=ticker, bars=bars[: end + 1], entry_price=entry_price)
        )
        if signal is not None and signal.kind in {"sell", "exit"}:
            return signal.kind
    return None


MARKET_REFERENCE = ("SBER", "GAZP", "LKOH")


def last_day(ticker: str) -> date | None:
    from app.strategy.backtest import load_bars

    path = Path(os.environ.get("CANDLE_DIR", "data/candles")) / f"{ticker}.csv"
    if not path.is_file():
        return None
    bars = load_bars(path)
    return bar_day(bars[-1]) if bars else None


def market_day() -> date | None:
    """Последний торговый день в файлах свечей — по самым ликвидным бумагам."""
    days = [day for day in map(last_day, MARKET_REFERENCE) if day is not None]
    return max(days) if days else None


def stale_holdings(tickers, day: date | None = None) -> list[dict]:
    """Бумаги в портфеле без свечи за последний торговый день.

    Решение о продаже по ним не принимается: стратегия не видит цену.
    """
    day = day or market_day()
    if day is None:
        return []
    out = []
    for ticker in sorted(tickers):
        seen = last_day(ticker)
        if seen is not None and seen >= day:
            continue
        out.append(
            {
                "ticker": ticker,
                "last_day": seen.isoformat() if seen else None,
                "days_behind": (day - seen).days if seen else None,
                "market_day": day.isoformat(),
            }
        )
    return out


def _trade_qty(row: dict) -> int | None:
    raw = row.get("qty")
    if raw is None or raw == "":
        return None
    try:
        return int(Decimal(str(raw)))
    except (ArithmeticError, ValueError):
        return None


def entry_day(trades: Sequence[dict], ticker: str, tz) -> date | None:
    """День первой покупки текущей позиции.

    Частичная продажа день входа не сбрасывает. Иначе выход ищется по последним
    30 барам без цены входа этой позиции и продаёт бумагу по сигналу, который
    был ещё до покупки. Полная продажа закрывает отсчёт. Сделка без qty —
    полный выход, как раньше.
    """
    qty = 0
    found: date | None = None
    symbol = ticker.strip().upper()
    for row in trades:
        if str(row.get("ticker") or "").upper() != symbol:
            continue
        side = row.get("side")
        traded = _trade_qty(row)
        if side == "buy":
            if qty <= 0 and found is None:
                try:
                    found = (
                        datetime.fromisoformat(str(row.get("ts")))
                        .astimezone(tz)
                        .date()
                    )
                except ValueError:
                    continue
            qty += 0 if traded is None else traded
            continue
        if side != "sell":
            continue
        if traded is None:
            qty = 0
            found = None
            continue
        qty -= traded
        if qty <= 0:
            qty = 0
            found = None
    return found
