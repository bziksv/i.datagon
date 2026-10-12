"""Рукав overnight_bounce: вечерний вход на слабости, тейк на следующий день.

Что ломало первую версию:
- покупка каждый вечер без фильтра → вход в тренд вниз;
- докуп раздувал убыток, стоп считался от средней;
- после тейка тот же вечер покупали на хае;
- мелкие тейки не перекрывали редкие крупные стопы.

Текущие правила (дневки / OHLC-модель):
- вход на close только если: красный день, день ≤ −min_day_drop,
  предыдущий день зелёный, close в нижней части диапазона, close ≤ SMA,
  RSI ≤ rsi_max;
- тейк по high на следующий день; стоп от первой цены входа;
- усреднение редко (2-й слой) и только на ещё одном красном дне;
- макс. удержание 2 бара (ночь + день); после стопа — пауза;
- после тейка/стопа в тот же вечер не входим.

На выборке MOEX blue chips это защитный overnight, не «печатный станок».
"""

from decimal import Decimal

from app.strategy.base import BarContext, Signal, Strategy

SLEEVE = "overnight_bounce"
TIMEFRAME = "1d"
DEFAULT_TAKE_PROFIT_PCT = Decimal("0.035")
DEFAULT_AVERAGE_TRIGGER_PCT = Decimal("0.04")
DEFAULT_MAX_LAYERS = 2
DEFAULT_STOP_PCT = Decimal("0.035")
DEFAULT_SMA_PERIOD = 5
DEFAULT_MAX_HOLD_BARS = 2
DEFAULT_COOLDOWN_BARS = 5
DEFAULT_MIN_DAY_DROP_PCT = Decimal("0.01")
DEFAULT_RSI_PERIOD = 14
DEFAULT_RSI_MAX = Decimal("40")
DEFAULT_CLOSE_RANGE_MAX = Decimal("0.40")  # close в нижних 40% дневного диапазона


def _sma(closes: list[Decimal], period: int) -> Decimal | None:
    if period < 1 or len(closes) < period:
        return None
    window = closes[-period:]
    return sum(window, Decimal("0")) / Decimal(period)


def _rsi(closes: list[Decimal], period: int) -> Decimal | None:
    if period < 1 or len(closes) < period + 1:
        return None
    gains = Decimal("0")
    losses = Decimal("0")
    for index in range(-period, 0):
        delta = closes[index] - closes[index - 1]
        if delta >= 0:
            gains += delta
        else:
            losses += -delta
    if losses == 0:
        return Decimal("100")
    rs = gains / losses
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


class OvernightBounceStrategy(Strategy):
    sleeve = SLEEVE
    timeframe = TIMEFRAME
    fill_at = "close"
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

    def _entry_allowed(self, ctx: BarContext) -> bool:
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
        # пока RSI не готов — не блокируем; когда готов — режем перекупленность
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
                kind="flat",
                ts=bar.ts,
            )
        drawdown = (entry - Decimal(bar.c)) / entry
        if (
            drawdown >= self.average_trigger_pct
            and self._layers < self.max_layers
            and self._weak_close(bar)
        ):
            self._layers += 1
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="buy",
                ts=bar.ts,
            )
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind="flat",
            ts=bar.ts,
        )

    def note_stop(self) -> None:
        """Движок бэктеста вызывает после стопа — включаем паузу."""
        self._cooldown_left = self.cooldown_bars
        self._cooldown_armed = True
        self._reset_position_state()
