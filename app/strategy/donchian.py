"""Рукав donchian_breakout: пробой канала за period баров → buy/sell/flat."""

from collections.abc import Sequence
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.base import BarContext, Signal, Strategy
from app.strategy.stop import DEFAULT_STOP_PCT, bar_hits_stop

SLEEVE = "donchian_breakout"
DEFAULT_PERIOD = 20


def donchian_kind(bars: Sequence[CandleBar], period: int) -> str:
    prior = bars[-(period + 1) : -1]
    last = bars[-1]
    upper = max(bar.h for bar in prior)
    lower = min(bar.low for bar in prior)
    if last.c > upper:
        return "buy"
    if last.c < lower:
        return "sell"
    return "flat"


class DonchianBreakoutStrategy(Strategy):
    sleeve = SLEEVE

    def __init__(
        self,
        period: int = DEFAULT_PERIOD,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
    ) -> None:
        self.period = period
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
        if len(ctx.bars) < self.period + 1:
            return None
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind=donchian_kind(ctx.bars, self.period),
            ts=ctx.bars[-1].ts,
        )
