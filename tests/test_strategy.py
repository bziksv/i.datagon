from datetime import UTC, datetime
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.base import BarContext, Strategy
from app.strategy.flat import FlatStrategy
from app.strategy.idle import IdleStrategy
from worker.strategy import dispatch


def _bar() -> CandleBar:
    return CandleBar(
        ts=datetime(2026, 10, 12, 0, 0, tzinfo=UTC),
        o=Decimal("100"),
        h=Decimal("101"),
        low=Decimal("99"),
        c=Decimal("100.5"),
        v=Decimal("10"),
    )


def test_two_strategies_do_not_break_worker() -> None:
    ctx = BarContext(ticker="SBER", bars=[_bar()])
    sleeves: list[Strategy] = [IdleStrategy(), FlatStrategy()]
    got = dispatch(sleeves, ctx)
    assert got[0] is None
    assert got[1] is not None
    assert got[1].kind == "flat"
    assert got[1].ticker == "SBER"
    assert got[1].sleeve == "flat"
