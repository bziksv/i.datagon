"""Решение на баре → строка signals."""

from collections.abc import Sequence

from app.models import SignalRow
from app.strategy.base import Signal


def row_from_signal(signal: Signal, payload: dict | None = None) -> SignalRow:
    return SignalRow(
        sleeve=signal.sleeve,
        ticker=signal.ticker,
        ts=signal.ts,
        kind=signal.kind,
        payload=payload if payload is not None else {},
    )


def record_decisions(signals: Sequence[Signal | None]) -> list[SignalRow]:
    return [row_from_signal(signal) for signal in signals if signal is not None]
