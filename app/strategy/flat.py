"""Второй рукав-заглушка: на каждом баре flat."""

from app.strategy.base import BarContext, Signal, Strategy


class FlatStrategy(Strategy):
    sleeve = "flat"

    def on_bar(self, ctx: BarContext) -> Signal | None:
        if not ctx.bars:
            return None
        return Signal(
            sleeve=self.sleeve,
            ticker=ctx.ticker,
            kind="flat",
            ts=ctx.bars[-1].ts,
        )
