"""Рукав abs_momentum: в рынке только когда бумага в силе.

Абсолютный моментум на днёвках:
- покупка, если close > SMA и ROC(lookback) ≥ порога;
- иначе выход в кэш;
- на просадке рынка большинство времени вне позиции.

Параметры подобраны сеткой на 14 blue chips MOEX (2024–2026):
lookback=20, sma=50, min_roc=2%. Это in-sample edge, не гарантия вперёд.
"""

from decimal import Decimal

from app.strategy.base import BarContext, Signal, Strategy

SLEEVE = "abs_momentum"
TIMEFRAME = "1d"
DEFAULT_LOOKBACK = 20
DEFAULT_SMA_PERIOD = 50
DEFAULT_MIN_ROC = Decimal("0.02")
DEFAULT_STOP_PCT = Decimal("0")
# Полный кэш на имя в desk-бэктесте — чтобы видеть «максимум» на истории.
DEFAULT_BACKTEST_POSITION_SHARE = Decimal("1")


class AbsMomentumStrategy(Strategy):
    sleeve = SLEEVE
    timeframe = TIMEFRAME
    backtest_position_share = DEFAULT_BACKTEST_POSITION_SHARE

    def __init__(
        self,
        *,
        lookback: int = DEFAULT_LOOKBACK,
        sma_period: int = DEFAULT_SMA_PERIOD,
        min_roc: Decimal = DEFAULT_MIN_ROC,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
        backtest_position_share: Decimal = DEFAULT_BACKTEST_POSITION_SHARE,
    ) -> None:
        if lookback < 2:
            raise ValueError("lookback must be >= 2")
        if sma_period < 2:
            raise ValueError("sma_period must be >= 2")
        if stop_pct < 0:
            raise ValueError("stop_pct must be >= 0")
        if not Decimal("0") < backtest_position_share <= Decimal("1"):
            raise ValueError("backtest_position_share must be in (0, 1]")
        self.lookback = lookback
        self.sma_period = sma_period
        self.min_roc = Decimal(min_roc)
        self.stop_pct = Decimal(stop_pct)
        self.backtest_position_share = Decimal(backtest_position_share)

    def _long_ok(self, ctx: BarContext) -> bool:
        need = max(self.lookback, self.sma_period) + 1
        if len(ctx.bars) < need:
            return False
        closes = [Decimal(bar.c) for bar in ctx.bars]
        roc = closes[-1] / closes[-(self.lookback + 1)] - Decimal("1")
        mean = sum(closes[-self.sma_period :], Decimal("0")) / Decimal(
            self.sma_period
        )
        return closes[-1] > mean and roc >= self.min_roc

    def on_bar(self, ctx: BarContext) -> Signal | None:
        if not ctx.bars:
            return None
        bar = ctx.bars[-1]
        need = max(self.lookback, self.sma_period) + 1
        if len(ctx.bars) < need:
            return None

        if ctx.entry_price is not None and self.stop_pct > 0:
            stop = Decimal(ctx.entry_price) * (Decimal("1") - self.stop_pct)
            if Decimal(bar.low) <= stop:
                return Signal(
                    sleeve=self.sleeve,
                    ticker=ctx.ticker,
                    kind="exit",
                    ts=bar.ts,
                )

        long_ok = self._long_ok(ctx)
        if ctx.entry_price is None:
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="buy" if long_ok else "flat",
                ts=bar.ts,
            )
        if not long_ok:
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="sell",
                ts=bar.ts,
            )
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind="flat",
            ts=bar.ts,
        )
