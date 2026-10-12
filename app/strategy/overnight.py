"""Рукав overnight_bounce: покупка на закрытии, тейк днём, усреднение вечером.

Идея (дневки, модель на OHLC):
- вечером, если позиции нет — покупка по цене закрытия;
- на следующих днях, если high дотягивает до take-profit от средней цены —
  продажа внутри дня по уровню тейка (в бэктесте);
- если тейк не взят и закрытие ушло ниже средней на average_trigger —
  вечерний докуп (усреднение), пока не исчерпан max_layers;
- жёсткий стоп от средней цены ограничивает «усреднение в пропасть».

Это paper-модель по дневному бару, не гарантия внутридневного исполнения.
"""

from decimal import Decimal

from app.strategy.base import BarContext, Signal, Strategy

SLEEVE = "overnight_bounce"
TIMEFRAME = "1d"
DEFAULT_TAKE_PROFIT_PCT = Decimal("0.045")  # середина коридора 3–6%
DEFAULT_AVERAGE_TRIGGER_PCT = Decimal("0.02")
DEFAULT_MAX_LAYERS = 3
DEFAULT_STOP_PCT = Decimal("0.10")


class OvernightBounceStrategy(Strategy):
    sleeve = SLEEVE
    timeframe = TIMEFRAME
    fill_at = "close"
    allow_add = True

    def __init__(
        self,
        *,
        take_profit_pct: Decimal = DEFAULT_TAKE_PROFIT_PCT,
        average_trigger_pct: Decimal = DEFAULT_AVERAGE_TRIGGER_PCT,
        max_layers: int = DEFAULT_MAX_LAYERS,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
    ) -> None:
        if take_profit_pct <= 0:
            raise ValueError("take_profit_pct must be > 0")
        if average_trigger_pct <= 0:
            raise ValueError("average_trigger_pct must be > 0")
        if max_layers < 1:
            raise ValueError("max_layers must be >= 1")
        if stop_pct < 0:
            raise ValueError("stop_pct must be >= 0")
        self.take_profit_pct = take_profit_pct
        self.average_trigger_pct = average_trigger_pct
        self.max_layers = max_layers
        self.stop_pct = stop_pct
        self._layers = 0
        self._ticker: str | None = None

    def _reset_if_needed(self, ticker: str, flat: bool) -> None:
        if flat or self._ticker != ticker:
            self._layers = 0
            self._ticker = ticker

    def on_bar(self, ctx: BarContext) -> Signal | None:
        if not ctx.bars:
            return None
        bar = ctx.bars[-1]
        flat = ctx.entry_price is None
        self._reset_if_needed(ctx.ticker, flat)

        if flat:
            self._layers = 1
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="buy",
                ts=bar.ts,
            )

        # Стоп и тейк исполняет движок бэктеста по low/high.
        # Здесь только вечернее усреднение при просадке закрытия.
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
        ):
            self._layers += 1
            return Signal(
                sleeve=self.sleeve,
                ticker=ctx.ticker,
                kind="buy",
                ts=bar.ts,
            )
        if self._layers < 1:
            self._layers = 1
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind="flat",
            ts=bar.ts,
        )
