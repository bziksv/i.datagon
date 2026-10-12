"""Рукав-заглушка: бар видит, сигнала нет."""

from app.strategy.base import BarContext, Signal, Strategy


class IdleStrategy(Strategy):
    def on_bar(self, ctx: BarContext) -> Signal | None:
        return None
