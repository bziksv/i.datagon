"""Бэктест-на-столе: свечи из файла, без брокера."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.broker.port import CandleBar
from app.strategy.base import BarContext, Signal, Strategy


def load_bars(path: Path) -> list[CandleBar]:
    lines = path.read_text().splitlines()
    bars: list[CandleBar] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        ts, o, h, low, c, v = line.split(",")
        bars.append(
            CandleBar(
                ts=datetime.fromisoformat(ts),
                o=Decimal(o),
                h=Decimal(h),
                low=Decimal(low),
                c=Decimal(c),
                v=Decimal(v),
            )
        )
    return bars


def replay(
    strategy: Strategy,
    ticker: str,
    bars: Sequence[CandleBar],
) -> list[Signal]:
    signals: list[Signal] = []
    for end in range(1, len(bars) + 1):
        got = strategy.on_bar(BarContext(ticker, bars[:end]))
        if got is not None:
            signals.append(got)
    return signals
