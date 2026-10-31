"""Рукав abs_momentum: в рынке только когда бумага в силе.

Абсолютный моментум на днёвках:
- вход: close > SMA, ROC(lookback) ≥ порога и бумага не перегрета (close/SMA);
- выход по силе мягче входа (гистерезис по ROC) — даём тренду дышать;
- трейлинг от пика close;
- на слабости — кэш.

Параметры — сетка на MOEX + S&P 500 desk (2024–2026), критерий:
плюс на обеих вселенных и max min(MOEX, SP). In-sample, не гарантия вперёд.
"""

from datetime import UTC, datetime, time
from decimal import Decimal
from pathlib import Path

from app.strategy.base import BarContext, Signal, Strategy

SLEEVE = "abs_momentum"
SLEEVE_V2 = "abs_momentum_2"
SLEEVE_V3 = "abs_momentum_3"
SLEEVE_V4 = "abs_momentum_4"
SLEEVE_V5 = "abs_momentum_5"
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
        vol_mult: Decimal = Decimal("1"),
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
        self.vol_mult = Decimal(vol_mult)
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
                if avg <= 0 or last < avg * self.vol_mult:
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
    """Короче тренд и дольше держим слабый день, чем вторая версия.

    Сетка TQBR 2024–2026, 177k вариантов: SMA30, ROC15 ≥ 0, выход после
    четырёх дней с ROC < −1%, оборот от 60% среднего за 20 дней.
    Широта, потолок дня и трейл после +20% те же. In-sample, не прогноз.
    """

    sleeve = SLEEVE_V3

    def __init__(self, **kwargs):
        kwargs.setdefault("lookback", 15)
        kwargs.setdefault("sma_period", 30)
        kwargs.setdefault("min_roc", Decimal("0"))
        kwargs.setdefault("exit_roc", Decimal("-0.01"))
        kwargs.setdefault("exit_streak", 4)
        kwargs.setdefault("vol_mult", Decimal("0.6"))
        super().__init__(**kwargs)


class AbsMomentum4Strategy(AbsMomentum3Strategy):
    """Те же правила, что у третьей, но широта 42% вместо 45%.

    На сетке в 251 тысячу вариантов остальное не обогнало третью версию,
    если держать обе половины выборки. In-sample, не прогноз.
    """

    sleeve = SLEEVE_V4

    def __init__(self, **kwargs):
        kwargs.setdefault("breadth_min", Decimal("0.42"))
        super().__init__(**kwargs)


# Пятая версия — не дневной фильтр, а оборот внутри дня на 10-минутках.
# Сетка на ликвидном TQBR (2024–H1 2025 обучение, дальше проверка):
# откат от локального хая в уже растущей бумаге, тейк около 1.2%, стоп короче.
# Сетка на 10-минутках ликвидного TQBR: тейк 1–2% с выходом каждый вечер
# проигрывал удержанию. Оставлен вариант, который меньше теряет на той же
# выборке: вход с отката, выход когда цена теряет среднюю, стоп 4%.
V5_TREND_BARS = 80
V5_ROC_BARS = 24
V5_MIN_ROC = Decimal("0")
V5_DIP_BARS = 6
V5_PULLBACK = Decimal("0.012")
V5_MAX_PULLBACK = Decimal("0.05")
V5_TAKE_PROFIT = Decimal("0")
V5_STOP = Decimal("0.04")
V5_COOLDOWN_BARS = 1
V5_MAX_TRADES_PER_DAY = 6
# MOEX 10:00–18:40 МСК = 07:00–15:40 UTC. Новые входы не позже 17:00 МСК.
V5_SESSION_OPEN = time(7, 0)
V5_LAST_ENTRY = time(14, 0)
V5_FLAT_AFTER = time(15, 20)


def _as_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC)


class AbsMomentum5Strategy(Strategy):
    """Внутридневный моментум на 10-минутках.

    Вход: бумага уже выше средней, зелёный бар после отката от локального
    максимума. Выход: close снова под средней или стоп. Вечерний выход
    выключен — ночное движение на истории было дороже, чем тейк 1–2%.
    Если позиция закрылась, в тот же день можно зайти снова.
    """

    sleeve = SLEEVE_V5
    timeframe = "10m"
    fill_at = "next_open"
    backtest_position_share = DEFAULT_BACKTEST_POSITION_SHARE

    def __init__(
        self,
        *,
        trend_bars: int = V5_TREND_BARS,
        roc_bars: int = V5_ROC_BARS,
        min_roc: Decimal = V5_MIN_ROC,
        dip_bars: int = V5_DIP_BARS,
        pullback: Decimal = V5_PULLBACK,
        max_pullback: Decimal = V5_MAX_PULLBACK,
        take_profit_pct: Decimal = V5_TAKE_PROFIT,
        stop_pct: Decimal = V5_STOP,
        cooldown_bars: int = V5_COOLDOWN_BARS,
        max_trades_per_day: int = V5_MAX_TRADES_PER_DAY,
        style: str = "ride",
        hold_overnight: bool = True,
        session_open: time = V5_SESSION_OPEN,
        last_entry: time = V5_LAST_ENTRY,
        flat_after: time = V5_FLAT_AFTER,
        backtest_position_share: Decimal = DEFAULT_BACKTEST_POSITION_SHARE,
    ) -> None:
        if trend_bars < 2 or roc_bars < 1 or dip_bars < 2:
            raise ValueError("windows must be positive")
        if not Decimal("0") < backtest_position_share <= Decimal("1"):
            raise ValueError("backtest_position_share must be in (0, 1]")
        self.trend_bars = trend_bars
        self.roc_bars = roc_bars
        self.min_roc = Decimal(min_roc)
        self.dip_bars = dip_bars
        self.pullback = Decimal(pullback)
        self.max_pullback = Decimal(max_pullback)
        self.take_profit_pct = Decimal(take_profit_pct)
        self.stop_pct = Decimal(stop_pct)
        if style not in {"pullback", "breakout", "ride"}:
            raise ValueError("style")
        self.cooldown_bars = cooldown_bars
        self.max_trades_per_day = max_trades_per_day
        self.style = style
        self.hold_overnight = hold_overnight
        self.session_open = session_open
        self.last_entry = last_entry
        self.flat_after = flat_after
        self.backtest_position_share = Decimal(backtest_position_share)
        self._ticker: str | None = None
        self._day: object = None
        self._trades_today = 0
        self._cooldown = 0
        self._was_in = False

    def _reset_ticker(self, ticker: str, day) -> None:
        if self._ticker != ticker:
            self._ticker = ticker
            self._cooldown = 0
            self._was_in = False
            self._trades_today = 0
            self._day = day
        elif self._day != day:
            self._day = day
            self._trades_today = 0

    def on_bar(self, ctx: BarContext) -> Signal | None:
        if not ctx.bars:
            return None
        bar = ctx.bars[-1]
        stamp = _as_utc(bar.ts)
        self._reset_ticker(ctx.ticker, stamp.date())
        in_position = ctx.entry_price is not None
        just_flat = self._was_in and not in_position
        self._was_in = in_position
        if just_flat:
            self._cooldown = self.cooldown_bars
        elif self._cooldown > 0 and not in_position:
            self._cooldown -= 1

        clock = stamp.time()
        if in_position and not self.hold_overnight and clock >= self.flat_after:
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="exit",
                ts=bar.ts,
            )
        if (
            in_position
            and self.style == "ride"
            and len(ctx.bars) >= self.trend_bars
        ):
            trend = ctx.bars[-self.trend_bars :]
            mean = sum((Decimal(item.c) for item in trend), Decimal("0")) / Decimal(
                self.trend_bars
            )
            if Decimal(bar.c) < mean:
                return Signal(
                    sleeve=self.sleeve,
                    ticker=ctx.ticker,
                    kind="exit",
                    ts=bar.ts,
                )
        if in_position or clock < self.session_open or clock >= self.last_entry:
            return None
        if self._cooldown > 0 or self._trades_today >= self.max_trades_per_day:
            return None
        need = max(self.trend_bars, self.roc_bars + 1, self.dip_bars)
        if len(ctx.bars) < need:
            return None
        window = ctx.bars[-self.trend_bars :]
        closes = [Decimal(item.c) for item in window]
        close = closes[-1]
        mean = sum(closes, Decimal("0")) / Decimal(self.trend_bars)
        base = Decimal(ctx.bars[-(self.roc_bars + 1)].c)
        if mean <= 0 or base <= 0 or close <= mean:
            return None
        roc = close / base - Decimal("1")
        if roc < self.min_roc:
            return None
        recent = ctx.bars[-self.dip_bars :]
        if self.style == "breakout":
            prior = recent[:-1]
            if not prior:
                return None
            peak = max(Decimal(item.h) for item in prior)
            if peak <= 0 or close < peak:
                return None
        else:
            peak = max(Decimal(item.h) for item in recent)
            if peak <= 0:
                return None
            dip = Decimal("1") - close / peak
            if dip < self.pullback or dip > self.max_pullback:
                return None
        if close <= Decimal(bar.o):
            return None
        prev = Decimal(ctx.bars[-2].c)
        if close <= prev:
            return None
        self._trades_today += 1
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind="buy",
            ts=bar.ts,
        )
