"""Рукав ema_scalp: M15, быстрый EMA-кросс, короткий стоп."""

from collections.abc import Sequence
from decimal import Decimal

from app.strategy.base import BarContext, Signal, Strategy
from app.strategy.stop import bar_hits_stop

SLEEVE = "ema_scalp"
DEFAULT_FAST = 3
DEFAULT_SLOW = 8
DEFAULT_STOP_PCT = Decimal("0.015")
TIMEFRAME = "15m"


def ema(closes: Sequence[Decimal], period: int) -> Decimal:
    if period < 1 or len(closes) < period:
        raise ValueError("not enough closes")
    seed = sum(closes[:period], Decimal("0")) / Decimal(period)
    alpha = Decimal("2") / (Decimal(period) + Decimal("1"))
    value = seed
    for price in closes[period:]:
        value = alpha * price + (Decimal("1") - alpha) * value
    return value


def ema_kind(
    closes: Sequence[Decimal],
    *,
    fast: int,
    slow: int,
) -> str | None:
    need = slow + 1
    if len(closes) < need:
        return None
    fast_now = ema(closes, fast)
    slow_now = ema(closes, slow)
    fast_prev = ema(closes[:-1], fast)
    slow_prev = ema(closes[:-1], slow)
    if fast_prev <= slow_prev and fast_now > slow_now:
        return "buy"
    if fast_prev >= slow_prev and fast_now < slow_now:
        return "sell"
    return "flat"


class EmaScalpStrategy(Strategy):
    sleeve = SLEEVE
    timeframe = TIMEFRAME

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
        closes = [bar.c for bar in ctx.bars]
        kind = ema_kind(closes, fast=self.fast, slow=self.slow)
        if kind is None:
            return None
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind=kind,
            ts=ctx.bars[-1].ts,
        )
