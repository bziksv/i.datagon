from datetime import UTC, datetime
from decimal import Decimal

from app.broker.port import CandleBar
from app.strategy.base import BarContext
from app.strategy.flat import FlatStrategy
from app.strategy.idle import IdleStrategy
from app.strategy.signals import record_decisions
from worker.strategy import dispatch


def _bar() -> CandleBar:
    return CandleBar(
        ts=datetime(2026, 1, 10, tzinfo=UTC),
        o=Decimal("100"),
        h=Decimal("101"),
        low=Decimal("99"),
        c=Decimal("100.5"),
        v=Decimal("10"),
    )


def test_decision_bar_is_written() -> None:
    ctx = BarContext("SBER", [_bar()])
    decided = dispatch([IdleStrategy(), FlatStrategy()], ctx)
    rows = record_decisions(decided)
    assert len(rows) == 1
    assert rows[0].sleeve == "flat"
    assert rows[0].ticker == "SBER"
    assert rows[0].kind == "flat"
    assert rows[0].ts == ctx.bars[-1].ts
    assert rows[0].payload == {}
