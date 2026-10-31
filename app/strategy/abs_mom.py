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
# День, которого не было даже после перечитывания файлов: второй раз не долбим диск.
_BREADTH_MISS: set[str] = set()
_SP_BREADTH_MISS: set[str] = set()


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
    """Доля бумаг TQBR с close > SMA40 на дату свечи. Кэш сбрасывает session_breadth."""
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


def _market(ticker: str) -> str:
    import os

    symbol = (ticker or "").strip().upper()
    moex = Path(os.environ.get("CANDLE_DIR", "data/candles")) / f"{symbol}.csv"
    sp = Path(os.environ.get("CANDLE_SP500_DIR", "data/candles_sp500")) / f"{symbol}.csv"
    if symbol and sp.is_file() and not moex.is_file():
        return "sp"
    return "tqbr"


def breadth_for(ticker: str) -> dict[str, float]:
    """Широта того рынка, откуда взята бумага. S&P не смотрит календарь TQBR."""
    if _market(ticker) == "sp":
        return sp500_breadth()
    return tqbr_breadth()


def session_breadth(ticker: str, key: str) -> float | None:
    """Широта на дату бара. None — справочника нет, фильтр входа не включаем.

    Воркер не перезапускается сутками. Кэш, собранный на закрытии одного дня,
    не содержит следующую сессию: пропуск ключа читался как 0, и при пороге
    42% не проходила ни одна покупка. Если дня в кэше нет — один раз перечитать
    файлы свечей, которые к закрытию уже докачаны.
    """
    global _BREADTH, _SP_BREADTH
    market = _market(ticker)
    missed = _SP_BREADTH_MISS if market == "sp" else _BREADTH_MISS
    book = sp500_breadth() if market == "sp" else tqbr_breadth()
    if key not in book and key not in missed:
        missed.add(key)
        if market == "sp":
            _SP_BREADTH = None
        else:
            _BREADTH = None
        book = sp500_breadth() if market == "sp" else tqbr_breadth()
    if not book:
        return None
    return float(book.get(key, 0.0))


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
                key = ctx.bars[-1].ts.date().isoformat()
                breadth = session_breadth(ctx.ticker, key)
                if breadth is not None and breadth < float(self.breadth_min):
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


# Бумаги, которые в бэктесте считаем доступными для шорта в Т-Банке:
# ядро прогона и ликвидные голубые фишки. Список можно подменить.
def default_shortable() -> frozenset[str]:
    from app.strategy.moex_groups import MOEX_DESK_CORE

    extra = (
        "AFKS",
        "AFLT",
        "HYDR",
        "IRAO",
        "MAGN",
        "MTSS",
        "NLMK",
        "PHOR",
        "PIKK",
        "SBERP",
        "SNGSP",
        "TATNP",
        "VKCO",
    )
    return frozenset(MOEX_DESK_CORE).union(extra)


class AbsMomentum5Strategy(AbsMomentum4Strategy):
    """Те же длинные правила, что у четвёртой версии, плюс зеркальный шорт.

    Шорты выключены — сигналы совпадают с моментумом-4. Включены — в слабой
    бумаге при узкой широте рынка открывается короткая позиция. Выход зеркальный:
    серия дней с ростом ROC, трейл от минимума после прибыли, стоп выше входа.
    """

    sleeve = SLEEVE_V5

    def __init__(
        self,
        *,
        shorts_enabled: bool = False,
        longs_enabled: bool = True,
        short_breadth_max: Decimal = Decimal("0.42"),
        short_stop_pct: Decimal = Decimal("0"),
        max_short_exposure: Decimal = Decimal("1"),
        shortable: frozenset[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.shorts_enabled = bool(shorts_enabled)
        self.allow_short = self.shorts_enabled
        self.longs_enabled = bool(longs_enabled)
        self.short_breadth_max = Decimal(short_breadth_max)
        self.short_stop_pct = Decimal(short_stop_pct)
        self.max_short_exposure = Decimal(max_short_exposure)
        self.shortable = shortable if shortable is not None else default_shortable()
        self._short_weak = 0
        self._short_trough: Decimal | None = None

    def _sync_ticker(self, ticker: str) -> None:
        changed = self._ticker != ticker
        super()._sync_ticker(ticker)
        if changed:
            self._short_weak = 0
            self._short_trough = None

    def _shortable(self, ticker: str) -> bool:
        return ticker.strip().upper() in self.shortable

    def _volume_ok(self, ctx: BarContext, close: Decimal) -> bool:
        if not self.require_volume:
            return True
        bars = ctx.bars
        if len(bars) < 21:
            return False
        last = Decimal(bars[-1].v) * close
        avg = sum(
            (Decimal(bar.v) * Decimal(bar.c) for bar in bars[-21:-1]),
            Decimal("0"),
        ) / Decimal(20)
        return avg > 0 and last >= avg * self.vol_mult

    def _short_entry_ok(self, ctx: BarContext) -> bool:
        if not self._shortable(ctx.ticker):
            return False
        packed = self._sma_and_roc(ctx)
        if packed is None:
            return False
        close, mean, roc = packed
        if mean <= 0 or close >= mean or roc > -self.min_roc:
            return False
        if self.max_stretch > 0 and close / mean < Decimal("1") / self.max_stretch:
            return False
        if not self._volume_ok(ctx, close):
            return False
        if self.max_day_up > 0 and len(ctx.bars) >= 2:
            prev = Decimal(ctx.bars[-2].c)
            if prev > 0 and close / prev - Decimal("1") < -self.max_day_up:
                return False
        if self.short_breadth_max < Decimal("1"):
            key = ctx.bars[-1].ts.date().isoformat()
            breadth = session_breadth(ctx.ticker, key)
            if breadth is None or breadth > float(self.short_breadth_max):
                return False
        return True

    def _short_exit(self, ctx: BarContext) -> Signal | None:
        bar = ctx.bars[-1]
        entry = Decimal(ctx.entry_price or "0")
        close = Decimal(bar.c)
        self._short_trough = (
            close if self._short_trough is None else min(self._short_trough, close)
        )
        armed = self.trail_arm <= 0 or (close > 0 and entry / close >= self.trail_arm)
        if (
            self._trail_base > 0
            and armed
            and close >= self._short_trough * (Decimal("1") + self._trail_base)
        ):
            self._short_trough = None
            self._short_weak = 0
            return Signal(self.sleeve, ctx.ticker, "exit", bar.ts)
        packed = self._sma_and_roc(ctx)
        if packed is not None:
            roc = packed[2]
            if roc <= -self.exit_roc:
                self._short_weak = 0
            else:
                self._short_weak += 1
                if self._short_weak >= self.exit_streak:
                    self._short_trough = None
                    self._short_weak = 0
                    return Signal(self.sleeve, ctx.ticker, "exit", bar.ts)
        return None

    def on_bar(self, ctx: BarContext) -> Signal | None:
        if not self.shorts_enabled:
            return super().on_bar(ctx)
        if ctx.entry_price is not None and ctx.side == "short":
            return self._short_exit(ctx)
        if not self.longs_enabled:
            if ctx.entry_price is not None:
                return super().on_bar(ctx)
            if self._short_entry_ok(ctx):
                return Signal(self.sleeve, ctx.ticker, "short", ctx.bars[-1].ts)
            return None
        signal = super().on_bar(ctx)
        if ctx.entry_price is None and (
            signal is None or signal.kind != "buy"
        ) and self._short_entry_ok(ctx):
            return Signal(self.sleeve, ctx.ticker, "short", ctx.bars[-1].ts)
        return signal
