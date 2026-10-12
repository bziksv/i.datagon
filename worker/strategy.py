"""Воркер гоняет любые Strategy через один dispatch."""

from collections.abc import Sequence

from app.strategy.base import BarContext, Signal, Strategy


def dispatch(
    strategies: Sequence[Strategy],
    ctx: BarContext,
) -> list[Signal | None]:
    return [strategy.on_bar(ctx) for strategy in strategies]
