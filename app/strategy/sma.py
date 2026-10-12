"""Рукав sma_cross: дневки, быстрая и медленная SMA → buy/sell/flat."""

from collections.abc import Sequence
from decimal import Decimal

from app.strategy.base import BarContext, Signal, Strategy
from app.strategy.stop import DEFAULT_STOP_PCT, bar_hits_stop

SLEEVE = "sma_cross"
DEFAULT_FAST = 5
DEFAULT_SLOW = 20


def sma(closes: Sequence[Decimal], period: int) -> Decimal:
    window = closes[-period:]
    return sum(window, Decimal("0")) / Decimal(period)


def sma_kind(
    closes: Sequence[Decimal],
    *,
    fast: int,
    slow: int,
) -> str:
    fast_now = sma(closes, fast)
    slow_now = sma(closes, slow)
    fast_prev = sma(closes[:-1], fast)
    slow_prev = sma(closes[:-1], slow)
    if fast_prev <= slow_prev and fast_now > slow_now:
        return "buy"
    if fast_prev >= slow_prev and fast_now < slow_now:
        return "sell"
    return "flat"


class SmaCrossStrategy(Strategy):
    sleeve = SLEEVE

    def __init__(
        self,
        fast: int = DEFAULT_FAST,
        slow: int = DEFAULT_SLOW,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
    ) -> None:
        self.fast = fast
        self.slow = slow
        self.stop_pct = stop_pct

    def on_bar(self, ctx: BarContext) -> Signal | None:
        if (
            ctx.entry_price is not None
            and ctx.bars
            and bar_hits_stop(
                ctx.bars[-1],
                ctx.entry_price,
                side=ctx.side,
                stop_pct=self.stop_pct,
            )
        ):
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="exit",
                ts=ctx.bars[-1].ts,
            )
        if len(ctx.bars) < self.slow + 1:
            return None
        closes = [bar.c for bar in ctx.bars]
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind=sma_kind(closes, fast=self.fast, slow=self.slow),
            ts=ctx.bars[-1].ts,
        )
