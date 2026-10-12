"""Рукав morning_bounce: утренний докуп в противовес вечернему.

Зеркало overnight_bounce на дневках:
- вечером на слабости дня решаем войти → покупка на следующем open;
- днём тейк по high / стоп по low от первой цены;
- под вечер по умолчанию продаём (close);
- если ушли в минус ≥ average_trigger — не продаём, а утром докупаем
  (2-й слой), затем снова пытаемся выйти к вечеру;
- после стопа — пауза cooldown_bars.

Это paper-модель open/close, не тиковый стакан.
"""

from decimal import Decimal

from app.strategy.base import BarContext, Signal, Strategy
from app.strategy.overnight import (
    DEFAULT_AVERAGE_TRIGGER_PCT,
    DEFAULT_CLOSE_RANGE_MAX,
    DEFAULT_COOLDOWN_BARS,
    DEFAULT_MAX_LAYERS,
    DEFAULT_MIN_DAY_DROP_PCT,
    DEFAULT_RSI_MAX,
    DEFAULT_RSI_PERIOD,
    DEFAULT_SMA_PERIOD,
    DEFAULT_STOP_PCT,
    DEFAULT_TAKE_PROFIT_PCT,
    _rsi,
    _sma,
)

SLEEVE = "morning_bounce"
TIMEFRAME = "1d"
DEFAULT_MAX_HOLD_BARS = 2


class MorningBounceStrategy(Strategy):
    sleeve = SLEEVE
    timeframe = TIMEFRAME
    fill_at = "morning"  # buy → next open; sell/exit → same-day close
    allow_add = True
    stop_from_first = True

    def __init__(
        self,
        *,
        take_profit_pct: Decimal = DEFAULT_TAKE_PROFIT_PCT,
        average_trigger_pct: Decimal = DEFAULT_AVERAGE_TRIGGER_PCT,
        max_layers: int = DEFAULT_MAX_LAYERS,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
        sma_period: int = DEFAULT_SMA_PERIOD,
        max_hold_bars: int = DEFAULT_MAX_HOLD_BARS,
        cooldown_bars: int = DEFAULT_COOLDOWN_BARS,
        min_day_drop_pct: Decimal = DEFAULT_MIN_DAY_DROP_PCT,
        rsi_period: int = DEFAULT_RSI_PERIOD,
        rsi_max: Decimal = DEFAULT_RSI_MAX,
        close_range_max: Decimal = DEFAULT_CLOSE_RANGE_MAX,
    ) -> None:
        if take_profit_pct <= 0:
            raise ValueError("take_profit_pct must be > 0")
        if average_trigger_pct <= 0:
            raise ValueError("average_trigger_pct must be > 0")
        if max_layers < 1:
            raise ValueError("max_layers must be >= 1")
        if stop_pct < 0:
            raise ValueError("stop_pct must be >= 0")
        if sma_period < 1:
            raise ValueError("sma_period must be >= 1")
        if max_hold_bars < 1:
            raise ValueError("max_hold_bars must be >= 1")
        if cooldown_bars < 0:
            raise ValueError("cooldown_bars must be >= 0")
        if min_day_drop_pct < 0:
            raise ValueError("min_day_drop_pct must be >= 0")
        if rsi_period < 2:
            raise ValueError("rsi_period must be >= 2")
        if not Decimal("0") < close_range_max <= Decimal("1"):
            raise ValueError("close_range_max must be in (0, 1]")
        self.take_profit_pct = take_profit_pct
        self.average_trigger_pct = average_trigger_pct
        self.max_layers = max_layers
        self.stop_pct = stop_pct
        self.sma_period = sma_period
        self.max_hold_bars = max_hold_bars
        self.cooldown_bars = cooldown_bars
        self.min_day_drop_pct = min_day_drop_pct
        self.rsi_period = rsi_period
        self.rsi_max = rsi_max
        self.close_range_max = close_range_max
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

    def _weak_close(self, bar) -> bool:
        return Decimal(bar.c) < Decimal(bar.o)

    def _setup_allowed(self, ctx: BarContext) -> bool:
        """Слабый день → покупаем завтра на open."""
        bar = ctx.bars[-1]
        if self._cooldown_left > 0:
            return False
        if not self._weak_close(bar):
            return False
        open_price = Decimal(bar.o)
        if open_price <= 0:
            return False
        day_drop = (open_price - Decimal(bar.c)) / open_price
        if day_drop < self.min_day_drop_pct:
            return False
        if len(ctx.bars) < 2:
            return False
        prev = ctx.bars[-2]
        if not (Decimal(prev.c) > Decimal(prev.o)):
            return False
        high = Decimal(bar.h)
        low = Decimal(bar.low)
        span = high - low
        if span > 0:
            close_pos = (Decimal(bar.c) - low) / span
            if close_pos > self.close_range_max:
                return False
        closes = [Decimal(row.c) for row in ctx.bars]
        mean = _sma(closes, self.sma_period)
        if mean is None or Decimal(bar.c) > mean:
            return False
        rsi_value = _rsi(closes, self.rsi_period)
        if rsi_value is not None and rsi_value > self.rsi_max:
            return False
        return True

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
            if not self._setup_allowed(ctx):
                return Signal(
                    sleeve=self.sleeve,
                    ticker=ctx.ticker,
                    kind="flat",
                    ts=bar.ts,
                )
            # сигнал на утренний вход следующего дня
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="buy",
                ts=bar.ts,
            )

        # Уже в позиции (купили на open). Вечернее решение.
        self._hold_bars += 1
        if self._layers < 1:
            self._layers = 1

        if self._hold_bars >= self.max_hold_bars:
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="exit",
                ts=bar.ts,
            )

        entry = Decimal(ctx.entry_price)
        if entry <= 0:
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="exit",
                ts=bar.ts,
            )
        drawdown = (entry - Decimal(bar.c)) / entry
        if (
            drawdown >= self.average_trigger_pct
            and self._layers < self.max_layers
            and self._weak_close(bar)
        ):
            self._layers += 1
            # держим ночь и докупаем завтра на open
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="buy",
                ts=bar.ts,
            )
        # по умолчанию продаём под вечер
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind="exit",
            ts=bar.ts,
        )

    def note_stop(self) -> None:
        self._cooldown_left = self.cooldown_bars
        self._cooldown_armed = True
        self._reset_position_state()

    def note_entry(self) -> None:
        """Движок вызывает после утренней покупки нового слоя/входа."""
        if self._layers < 1:
            self._layers = 1
        if self._hold_bars < 1:
            self._hold_bars = 0  # вечерний on_bar сделает +1
