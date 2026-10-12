"""Интерфейс Strategy: on_bar(ctx) -> Signal | None."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.broker.port import CandleBar


@dataclass(frozen=True)
class Signal:
    sleeve: str
    ticker: str
    kind: str
    ts: datetime


@dataclass(frozen=True)
class BarContext:
    ticker: str
    bars: Sequence[CandleBar]
    entry_price: Decimal | None = None
    side: str = "buy"


class Strategy(ABC):
    @abstractmethod
    def on_bar(self, ctx: BarContext) -> Signal | None:
        raise NotImplementedError
