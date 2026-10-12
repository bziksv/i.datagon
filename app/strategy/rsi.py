"""Рукав rsi_reversion: дневки, RSI → buy в перепроданности, sell в перекупленности."""

from collections.abc import Sequence
from decimal import Decimal

from app.strategy.base import BarContext, Signal, Strategy
from app.strategy.stop import DEFAULT_STOP_PCT, bar_hits_stop

SLEEVE = "rsi_reversion"
DEFAULT_PERIOD = 14
DEFAULT_OVERSOLD = Decimal("30")
DEFAULT_OVERBOUGHT = Decimal("70")


def wilder_rsi(closes: Sequence[Decimal], period: int) -> Decimal | None:
    if period < 1 or len(closes) < period + 1:
        return None
    gains = Decimal("0")
    losses = Decimal("0")
    for i in range(-period, 0):
        delta = closes[i] - closes[i - 1]
        if delta >= 0:
            gains += delta
        else:
            losses -= delta
    avg_gain = gains / Decimal(period)
    avg_loss = losses / Decimal(period)
    if avg_loss == 0:
        return Decimal("100") if avg_gain > 0 else Decimal("50")
    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def rsi_kind(
    closes: Sequence[Decimal],
    *,
    period: int,
    oversold: Decimal,
    overbought: Decimal,
) -> str | None:
    value = wilder_rsi(closes, period)
    if value is None:
        return None
    if value <= oversold:
        return "buy"
    if value >= overbought:
        return "sell"
    return "flat"


class RsiReversionStrategy(Strategy):
    sleeve = SLEEVE
    timeframe = "1d"

    def __init__(
        self,
        period: int = DEFAULT_PERIOD,
        oversold: Decimal = DEFAULT_OVERSOLD,
        overbought: Decimal = DEFAULT_OVERBOUGHT,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
    ) -> None:
        self.period = period
        self.oversold = Decimal(oversold)
        self.overbought = Decimal(overbought)
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
        kind = rsi_kind(
            closes,
            period=self.period,
            oversold=self.oversold,
            overbought=self.overbought,
        )
        if kind is None:
            return None
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind=kind,
            ts=ctx.bars[-1].ts,
        )
