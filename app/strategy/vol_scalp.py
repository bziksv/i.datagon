"""Рукав vol_scalp: короткий M10-скальп на всплеске волатильности.

Схема:
- вход: выше SMA(trend) + ATR% растёт + импульсный зелёный;
- в минусе — усреднение слоями (−0.5%), но только пока ATR ещё живой;
- выход: тейк +1% от средней, либо возврат к средней (после max_layers
  или если уже 2+ слоя и волатильность ушла); стоп выкл.

Не путать с ema_scalp (кросс без тейка) и overnight (дневки).
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from app.strategy.base import BarContext, Signal, Strategy

SLEEVE = "vol_scalp"
TIMEFRAME = "10m"

DEFAULT_TAKE_PROFIT_PCT = Decimal("0.010")  # 1% в коридоре 1–2% — больше оборота
DEFAULT_AVERAGE_TRIGGER_PCT = Decimal("0.005")  # каждый −0.5% к средней — ещё слой
DEFAULT_MAX_LAYERS = 6  # жёстко усредняем дальше
DEFAULT_STOP_PCT = Decimal("0")  # не стопаем до тейка
DEFAULT_ATR_PERIOD = 14
DEFAULT_MIN_ATR_PCT = Decimal("0.0018")
DEFAULT_ATR_EXPAND = Decimal("1.08")
DEFAULT_ATR_NORM_BARS = 20
DEFAULT_MAX_HOLD_BARS = 0  # 0 = не выходить по времени
# После max_layers: 0 = держать до возврата к средней; >0 — аварийный выход по барам
DEFAULT_MAX_LAYER_HOLD_BARS = 0
DEFAULT_COOLDOWN_BARS = 0
DEFAULT_CLOSE_RANGE_MIN = Decimal("0.50")
DEFAULT_MIN_BODY_RATIO = Decimal("0.30")
DEFAULT_SOFT_LOSS_PCT = Decimal("0")
DEFAULT_BACKTEST_POSITION_SHARE = Decimal("0.18")  # бюджет на все слои
DEFAULT_REQUIRE_PULLBACK = False  # слабый бар перед входом — опционально
DEFAULT_TREND_BARS = 100  # 0 = выкл; иначе вход только выше SMA(N) на M10
# Основная сессия MOEX в UTC (MSK = UTC+3): 07:00–15:40
DEFAULT_SESSION_START_UTC = (7, 0)
DEFAULT_SESSION_END_UTC = (15, 40)


def _true_range(bar, prev_close: Decimal | None) -> Decimal:
    high = Decimal(bar.h)
    low = Decimal(bar.low)
    span = high - low
    if prev_close is None:
        return span
    return max(span, abs(high - prev_close), abs(low - prev_close))


def atr_pct_at(bars: Sequence, *, period: int, end: int) -> Decimal | None:
    """ATR%/close на баре `end` (включительно)."""
    if period < 1 or end < period or end >= len(bars):
        return None
    total = Decimal("0")
    for index in range(end - period + 1, end + 1):
        prev_close = Decimal(bars[index - 1].c)
        total += _true_range(bars[index], prev_close)
    atr = total / Decimal(period)
    close = Decimal(bars[end].c)
    if close <= 0:
        return None
    return atr / close


def atr_pct(bars: Sequence, *, period: int) -> Decimal | None:
    if not bars:
        return None
    return atr_pct_at(bars, period=period, end=len(bars) - 1)


class VolScalpStrategy(Strategy):
    sleeve = SLEEVE
    timeframe = TIMEFRAME
    fill_at = "next_open"
    allow_add = True
    stop_from_first = True

    def __init__(
        self,
        *,
        take_profit_pct: Decimal = DEFAULT_TAKE_PROFIT_PCT,
        average_trigger_pct: Decimal = DEFAULT_AVERAGE_TRIGGER_PCT,
        max_layers: int = DEFAULT_MAX_LAYERS,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
        atr_period: int = DEFAULT_ATR_PERIOD,
        min_atr_pct: Decimal = DEFAULT_MIN_ATR_PCT,
        atr_expand: Decimal = DEFAULT_ATR_EXPAND,
        atr_norm_bars: int = DEFAULT_ATR_NORM_BARS,
        max_hold_bars: int = DEFAULT_MAX_HOLD_BARS,
        max_layer_hold_bars: int = DEFAULT_MAX_LAYER_HOLD_BARS,
        cooldown_bars: int = DEFAULT_COOLDOWN_BARS,
        close_range_min: Decimal = DEFAULT_CLOSE_RANGE_MIN,
        min_body_ratio: Decimal = DEFAULT_MIN_BODY_RATIO,
        soft_loss_pct: Decimal = DEFAULT_SOFT_LOSS_PCT,
        backtest_position_share: Decimal = DEFAULT_BACKTEST_POSITION_SHARE,
        require_pullback: bool = DEFAULT_REQUIRE_PULLBACK,
        trend_bars: int = DEFAULT_TREND_BARS,
        session_start_utc: tuple[int, int] = DEFAULT_SESSION_START_UTC,
        session_end_utc: tuple[int, int] = DEFAULT_SESSION_END_UTC,
    ) -> None:
        if not Decimal("0") < take_profit_pct <= Decimal("0.05"):
            raise ValueError("take_profit_pct must be in (0, 0.05]")
        if average_trigger_pct <= 0:
            raise ValueError("average_trigger_pct must be > 0")
        if max_layers < 1:
            raise ValueError("max_layers must be >= 1")
        if stop_pct < 0:
            raise ValueError("stop_pct must be >= 0")
        if atr_period < 2:
            raise ValueError("atr_period must be >= 2")
        if min_atr_pct <= 0:
            raise ValueError("min_atr_pct must be > 0")
        if atr_expand < 1:
            raise ValueError("atr_expand must be >= 1")
        if atr_norm_bars < 2:
            raise ValueError("atr_norm_bars must be >= 2")
        if max_hold_bars < 0:
            raise ValueError("max_hold_bars must be >= 0")
        if max_layer_hold_bars < 0:
            raise ValueError("max_layer_hold_bars must be >= 0")
        if cooldown_bars < 0:
            raise ValueError("cooldown_bars must be >= 0")
        if not Decimal("0") <= close_range_min <= Decimal("1"):
            raise ValueError("close_range_min must be in [0, 1]")
        if not Decimal("0") <= min_body_ratio <= Decimal("1"):
            raise ValueError("min_body_ratio must be in [0, 1]")
        if soft_loss_pct < 0:
            raise ValueError("soft_loss_pct must be >= 0")
        if not Decimal("0") < backtest_position_share <= Decimal("1"):
            raise ValueError("backtest_position_share must be in (0, 1]")
        if trend_bars < 0:
            raise ValueError("trend_bars must be >= 0")
        self.take_profit_pct = take_profit_pct
        self.average_trigger_pct = average_trigger_pct
        self.max_layers = max_layers
        self.stop_pct = stop_pct
        self.atr_period = atr_period
        self.min_atr_pct = min_atr_pct
        self.atr_expand = atr_expand
        self.atr_norm_bars = atr_norm_bars
        self.max_hold_bars = max_hold_bars
        self.max_layer_hold_bars = max_layer_hold_bars
        self.cooldown_bars = cooldown_bars
        self.close_range_min = close_range_min
        self.min_body_ratio = min_body_ratio
        self.soft_loss_pct = soft_loss_pct
        self.backtest_position_share = Decimal(backtest_position_share)
        self.require_pullback = bool(require_pullback)
        self.trend_bars = trend_bars
        self.session_start_utc = session_start_utc
        self.session_end_utc = session_end_utc
        self._layers = 0
        self._hold_bars = 0
        self._cooldown_left = 0
        self._cooldown_armed = False
        self._ticker: str | None = None

    def _reset_position_state(self) -> None:
        self._layers = 0
        self._hold_bars = 0

    def _sync_ticker(self, ticker: str) -> None:
        if self._ticker != ticker:
            self._ticker = ticker
            self._reset_position_state()
            self._cooldown_left = 0
            self._cooldown_armed = False

    def _volatile(self, ctx: BarContext) -> bool:
        end = len(ctx.bars) - 1
        value = atr_pct_at(ctx.bars, period=self.atr_period, end=end)
        if value is None or value < self.min_atr_pct:
            return False
        ref_end = end - self.atr_norm_bars
        if ref_end < self.atr_period:
            return value >= self.min_atr_pct
        ref = atr_pct_at(ctx.bars, period=self.atr_period, end=ref_end)
        if ref is None or ref <= 0:
            return value >= self.min_atr_pct
        return value >= ref * self.atr_expand

    def _weak_bar(self, bar) -> bool:
        open_price = Decimal(bar.o)
        close = Decimal(bar.c)
        high = Decimal(bar.h)
        low = Decimal(bar.low)
        if close < open_price:
            return True
        span = high - low
        if span <= 0:
            return False
        return (close - low) / span <= Decimal("0.45")

    def _in_session(self, bar) -> bool:
        ts = bar.ts
        if ts.tzinfo is None:
            return True
        utc = ts.utctimetuple()
        minutes = utc.tm_hour * 60 + utc.tm_min
        start = self.session_start_utc[0] * 60 + self.session_start_utc[1]
        end = self.session_end_utc[0] * 60 + self.session_end_utc[1]
        return start <= minutes <= end

    def _impulse_bar(self, bar) -> bool:
        open_price = Decimal(bar.o)
        close = Decimal(bar.c)
        high = Decimal(bar.h)
        low = Decimal(bar.low)
        if close <= open_price:
            return False
        span = high - low
        if span <= 0 or close <= 0:
            return False
        if span / close < self.min_atr_pct:
            return False
        close_pos = (close - low) / span
        body = (close - open_price) / span
        return close_pos >= self.close_range_min and body >= self.min_body_ratio

    def _above_trend(self, ctx: BarContext) -> bool:
        n = self.trend_bars
        if n <= 0:
            return True
        if len(ctx.bars) < n:
            return False
        window = ctx.bars[-n:]
        avg = sum((Decimal(bar.c) for bar in window), Decimal("0")) / Decimal(n)
        return Decimal(ctx.bars[-1].c) >= avg

    def _entry_allowed(self, ctx: BarContext) -> bool:
        if self._cooldown_left > 0:
            return False
        if len(ctx.bars) < 2:
            return False
        bar = ctx.bars[-1]
        if not self._in_session(bar):
            return False
        if not self._volatile(ctx):
            return False
        if not self._above_trend(ctx):
            return False
        if self.require_pullback and not self._weak_bar(ctx.bars[-2]):
            return False
        return self._impulse_bar(bar)

    def on_bar(self, ctx: BarContext) -> Signal | None:
        if not ctx.bars:
            return None
        bar = ctx.bars[-1]
        self._sync_ticker(ctx.ticker)
        flat = ctx.entry_price is None

        if flat:
            self._reset_position_state()
            if self._cooldown_left > 0:
                if self._cooldown_armed:
                    self._cooldown_armed = False
                else:
                    self._cooldown_left -= 1
                return Signal(
                    sleeve=self.sleeve,
                    ticker=ctx.ticker,
                    kind="flat",
                    ts=bar.ts,
                )
            if not self._entry_allowed(ctx):
                return Signal(
                    sleeve=self.sleeve,
                    ticker=ctx.ticker,
                    kind="flat",
                    ts=bar.ts,
                )
            self._layers = 1
            self._hold_bars = 1
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="buy",
                ts=bar.ts,
            )

        self._hold_bars += 1
        if self._layers < 1:
            self._layers = 1

        entry = Decimal(ctx.entry_price)
        if entry <= 0:
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="flat",
                ts=bar.ts,
            )

        drawdown = (entry - Decimal(bar.c)) / entry

        # Жёсткий докуп: каждый шаг просадки к текущей средней — ещё слой,
        # но только пока рынок ещё «живой» (ATR). В тихий тренд вниз не
        # добиваем мешок до max_layers — иначе капитал зависает на месяцы.
        if (
            self.max_layers > 1
            and drawdown >= self.average_trigger_pct
            and self._layers < self.max_layers
            and self._volatile(ctx)
            and self._in_session(bar)
        ):
            self._layers += 1
            self._hold_bars = 1
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="buy",
                ts=bar.ts,
            )

        # Вернулись к средней: (а) все слои набраны — выходим;
        # (б) уже усредняли (2+) и волатильность ушла — не ждём тейк годами.
        if Decimal(bar.c) >= entry and (
            self._layers >= self.max_layers
            or (self._layers >= 2 and not self._volatile(ctx))
        ):
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="exit",
                ts=bar.ts,
            )

        # Долгий мешок после max_layers: освобождаем капитал (~10 сессий M10).
        if (
            self.max_layer_hold_bars > 0
            and self._layers >= self.max_layers
            and self._hold_bars >= self.max_layer_hold_bars
        ):
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="exit",
                ts=bar.ts,
            )

        if (
            self.soft_loss_pct > 0
            and self._layers >= self.max_layers
            and self._hold_bars >= max(self.max_hold_bars // 2, 2)
            and drawdown >= self.soft_loss_pct
            and not self._volatile(ctx)
        ):
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="exit",
                ts=bar.ts,
            )

        # 0 = держим до тейка/стопа; иначе аварийный выход по времени.
        if self.max_hold_bars > 0 and self._hold_bars >= self.max_hold_bars:
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="exit",
                ts=bar.ts,
            )
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind="flat",
            ts=bar.ts,
        )

    def note_stop(self) -> None:
        self._cooldown_left = self.cooldown_bars
        self._cooldown_armed = True
        self._reset_position_state()
