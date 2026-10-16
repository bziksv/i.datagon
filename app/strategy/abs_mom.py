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
from pathlib import Path

from app.strategy.base import BarContext, Signal, Strategy

SLEEVE = "abs_momentum"
SLEEVE_V2 = "abs_momentum_2"
SLEEVE_V3 = "abs_momentum_3"
TIMEFRAME = "1d"
DEFAULT_LOOKBACK = 20
DEFAULT_SMA_PERIOD = 40
DEFAULT_MIN_ROC = Decimal("0.02")
# Выход мягче входа: держим, пока ROC ≥ −1% (не ждём снова +2%).
DEFAULT_EXIT_ROC = Decimal("-0.01")
DEFAULT_STOP_PCT = Decimal("0")
DEFAULT_TRAIL_PCT = Decimal("0.10")
# Не докупать на растяжке: close/SMA > 1.10 → ждём отката к тренду.
DEFAULT_MAX_STRETCH = Decimal("1.10")
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


# Вторая версия, сетка на TQBR 2024–2026 (боевой бэктест +25.2%):
# вход тот же, плюс оборот, потолок дня +7% и широта рынка
# (не покупаем, если выше SMA40 меньше 45% списка);
# один слабый день по ROC ещё держим, выход со второго;
# прокол SMA не продаёт; трейл 4% включается после +20% от входа.
V2_EXIT_ROC = Decimal("-0.02")
V2_TRAIL_PCT = Decimal("0.04")
V2_TRAIL_ARM = Decimal("1.20")
V2_MAX_DAY_UP = Decimal("0.07")
V2_BREADTH_MIN = Decimal("0.45")
V2_EXIT_STREAK = 2

_BREADTH: dict[str, float] | None = None
_SP_BREADTH: dict[str, float] | None = None


def _breadth_from_dir(root: Path) -> dict[str, float]:
    above: dict[str, list[int]] = {}
    if root.is_dir():
        for path in root.glob("*.csv"):
            lines = path.read_text().splitlines()
            closes: list[float] = []
            days: list[str] = []
            for line in lines[1:]:
                if not line.strip():
                    continue
                parts = line.split(",")
                days.append(parts[0][:10])
                closes.append(float(parts[4]))
            if len(closes) < 41:
                continue
            for index in range(40, len(closes)):
                sma = sum(closes[index - 39 : index + 1]) / 40
                slot = above.setdefault(days[index], [0, 0])
                slot[1] += 1
                slot[0] += closes[index] > sma
    return {day: slot[0] / slot[1] for day, slot in above.items() if slot[1]}


def tqbr_breadth() -> dict[str, float]:
    """Доля бумаг TQBR с close > SMA40 на дату свечи. Считается один раз."""
    global _BREADTH
    if _BREADTH is None:
        import os

        root = Path(os.environ.get("CANDLE_DIR", "data/candles"))
        _BREADTH = _breadth_from_dir(root)
    return _BREADTH


def sp500_breadth() -> dict[str, float]:
    """Доля бумаг из data/candles_sp500 с close > SMA40. Их собственный календарь."""
    global _SP_BREADTH
    if _SP_BREADTH is None:
        import os

        root = Path(os.environ.get("CANDLE_SP500_DIR", "data/candles_sp500"))
        _SP_BREADTH = _breadth_from_dir(root)
    return _SP_BREADTH


def breadth_for(ticker: str) -> dict[str, float]:
    """Широта того рынка, откуда взята бумага. S&P не смотрит календарь TQBR."""
    import os

    symbol = (ticker or "").strip().upper()
    moex = Path(os.environ.get("CANDLE_DIR", "data/candles")) / f"{symbol}.csv"
    sp = Path(os.environ.get("CANDLE_SP500_DIR", "data/candles_sp500")) / f"{symbol}.csv"
    if symbol and sp.is_file() and not moex.is_file():
        return sp500_breadth()
    return tqbr_breadth()


class AbsMomentum2Strategy(AbsMomentumStrategy):
    sleeve = SLEEVE_V2

    def __init__(
        self,
        *,
        lookback: int = DEFAULT_LOOKBACK,
        sma_period: int = DEFAULT_SMA_PERIOD,
        min_roc: Decimal = DEFAULT_MIN_ROC,
        exit_roc: Decimal = V2_EXIT_ROC,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
        trail_pct: Decimal = V2_TRAIL_PCT,
        max_stretch: Decimal = DEFAULT_MAX_STRETCH,
        backtest_position_share: Decimal = DEFAULT_BACKTEST_POSITION_SHARE,
        trail_arm: Decimal = V2_TRAIL_ARM,
        require_volume: bool = True,
        max_day_up: Decimal = V2_MAX_DAY_UP,
        breadth_min: Decimal = V2_BREADTH_MIN,
        exit_streak: int = V2_EXIT_STREAK,
    ) -> None:
        super().__init__(
            lookback=lookback,
            sma_period=sma_period,
            min_roc=min_roc,
            exit_roc=exit_roc,
            stop_pct=stop_pct,
            trail_pct=trail_pct,
            max_stretch=max_stretch,
            backtest_position_share=backtest_position_share,
        )
        self._trail_base = self.trail_pct
        self.trail_arm = Decimal(trail_arm)
        self.require_volume = require_volume
        self.max_day_up = Decimal(max_day_up)
        self.breadth_min = Decimal(breadth_min)
        self.exit_streak = exit_streak
        self._armed = False
        self._weak = 0

    def _sync_ticker(self, ticker: str) -> None:
        changed = self._ticker != ticker
        super()._sync_ticker(ticker)
        if changed:
            self._armed = False
            self._weak = 0

    def _long_ok(self, ctx: BarContext, *, for_entry: bool) -> bool:
        packed = self._sma_and_roc(ctx)
        if packed is None:
            return False
        close, mean, roc = packed
        if for_entry:
            if close <= mean or roc < self.min_roc:
                return False
            if (
                self.max_stretch > 0
                and mean > 0
                and close / mean > self.max_stretch
            ):
                return False
            if self.require_volume:
                bars = ctx.bars
                if len(bars) < 21:
                    return False
                last = Decimal(bars[-1].v) * close
                avg = sum(
                    (Decimal(bar.v) * Decimal(bar.c) for bar in bars[-21:-1]),
                    Decimal("0"),
                ) / Decimal(20)
                if avg <= 0 or last < avg:
                    return False
            if self.max_day_up > 0 and len(ctx.bars) >= 2:
                prev = Decimal(ctx.bars[-2].c)
                if prev > 0 and close / prev - Decimal("1") > self.max_day_up:
                    return False
            if self.breadth_min > 0:
                book = breadth_for(ctx.ticker)
                if book:
                    key = ctx.bars[-1].ts.date().isoformat()
                    if book.get(key, 0) < float(self.breadth_min):
                        return False
            return True
        if roc >= self.exit_roc:
            self._weak = 0
            return True
        self._weak += 1
        return self._weak < self.exit_streak

    def on_bar(self, ctx: BarContext) -> Signal | None:
        if ctx.entry_price is None or not ctx.bars:
            self._armed = False
            self._weak = 0
            self.trail_pct = Decimal("0")
        else:
            entry = Decimal(ctx.entry_price)
            close = Decimal(ctx.bars[-1].c)
            if self.trail_arm <= 0 or (
                entry > 0 and close / entry >= self.trail_arm
            ):
                self._armed = True
            self.trail_pct = self._trail_base if self._armed else Decimal("0")
        return super().on_bar(ctx)


class AbsMomentum3Strategy(AbsMomentum2Strategy):
    """Те же правила, что у второй версии. Дальше дожимаем уже её."""

    sleeve = SLEEVE_V3
