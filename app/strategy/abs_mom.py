"""Рукав abs_momentum: в рынке только когда бумага в силе.

Абсолютный моментум на днёвках:
- вход: close > SMA, ROC(lookback) ≥ порога и бумага не перегрета (close/SMA);
- выход по силе мягче входа (гистерезис по ROC) — даём тренду дышать;
- трейлинг от пика close;
- на слабости — кэш.

Параметры — сетка на MOEX + S&P 500 desk (2024–2026), критерий:
плюс на обеих вселенных и max min(MOEX, SP). In-sample, не гарантия вперёд.
"""

from decimal import Decimal

from app.strategy.base import BarContext, Signal, Strategy

SLEEVE = "abs_momentum"
TIMEFRAME = "1d"
DEFAULT_LOOKBACK = 20
DEFAULT_SMA_PERIOD = 40
DEFAULT_MIN_ROC = Decimal("0.02")
# Выход мягче входа: держим, пока ROC ≥ 0 (не ждём снова +2%).
DEFAULT_EXIT_ROC = Decimal("0")
DEFAULT_STOP_PCT = Decimal("0")
DEFAULT_TRAIL_PCT = Decimal("0.10")
# Не докупать на растяжке: close/SMA > 1.12 → ждём отката к тренду.
DEFAULT_MAX_STRETCH = Decimal("1.12")
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
        exit_roc: Decimal = DEFAULT_EXIT_ROC,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
        trail_pct: Decimal = DEFAULT_TRAIL_PCT,
        max_stretch: Decimal = DEFAULT_MAX_STRETCH,
        backtest_position_share: Decimal = DEFAULT_BACKTEST_POSITION_SHARE,
    ) -> None:
        if lookback < 2:
            raise ValueError("lookback must be >= 2")
        if sma_period < 2:
            raise ValueError("sma_period must be >= 2")
        if stop_pct < 0:
            raise ValueError("stop_pct must be >= 0")
        if trail_pct < 0:
            raise ValueError("trail_pct must be >= 0")
        if max_stretch < 0:
            raise ValueError("max_stretch must be >= 0")
        if not Decimal("0") < backtest_position_share <= Decimal("1"):
            raise ValueError("backtest_position_share must be in (0, 1]")
        self.lookback = lookback
        self.sma_period = sma_period
        self.min_roc = Decimal(min_roc)
        self.exit_roc = Decimal(exit_roc)
        self.stop_pct = Decimal(stop_pct)
        self.trail_pct = Decimal(trail_pct)
        self.max_stretch = Decimal(max_stretch)
        self.backtest_position_share = Decimal(backtest_position_share)
        self._peak: Decimal | None = None
        self._ticker: str | None = None

    def _sync_ticker(self, ticker: str) -> None:
        if self._ticker != ticker:
            self._ticker = ticker
            self._peak = None

    def _sma_and_roc(self, ctx: BarContext) -> tuple[Decimal, Decimal, Decimal] | None:
        need = max(self.lookback, self.sma_period) + 1
        if len(ctx.bars) < need:
            return None
        closes = [Decimal(bar.c) for bar in ctx.bars]
        close = closes[-1]
        mean = sum(closes[-self.sma_period :], Decimal("0")) / Decimal(
            self.sma_period
        )
        roc = close / closes[-(self.lookback + 1)] - Decimal("1")
        return close, mean, roc

    def _long_ok(self, ctx: BarContext, *, for_entry: bool) -> bool:
        packed = self._sma_and_roc(ctx)
        if packed is None:
            return False
        close, mean, roc = packed
        if close <= mean:
            return False
        if for_entry:
            if roc < self.min_roc:
                return False
            if (
                self.max_stretch > 0
                and mean > 0
                and close / mean > self.max_stretch
            ):
                return False
            return True
        return roc >= self.exit_roc

    def on_bar(self, ctx: BarContext) -> Signal | None:
        if not ctx.bars:
            return None
        bar = ctx.bars[-1]
        self._sync_ticker(ctx.ticker)
        need = max(self.lookback, self.sma_period) + 1
        if len(ctx.bars) < need:
            return None

        if ctx.entry_price is None:
            self._peak = None
            long_ok = self._long_ok(ctx, for_entry=True)
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="buy" if long_ok else "flat",
                ts=bar.ts,
            )

        entry = Decimal(ctx.entry_price)
        close = Decimal(bar.c)
        # Пик по close (дневная модель): intraday high слишком рано срывает тренд.
        self._peak = max(self._peak or entry, close)

        if self.stop_pct > 0 and Decimal(bar.low) <= entry * (
            Decimal("1") - self.stop_pct
        ):
            self._peak = None
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="exit",
                ts=bar.ts,
            )
        if (
            self.trail_pct > 0
            and self._peak is not None
            and close <= self._peak * (Decimal("1") - self.trail_pct)
        ):
            self._peak = None
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="exit",
                ts=bar.ts,
            )

        if not self._long_ok(ctx, for_entry=False):
            self._peak = None
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
