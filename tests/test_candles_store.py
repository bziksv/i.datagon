from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.broker.candles import new_candle_rows
from app.broker.port import CandleBar
from app.broker.tinkoff import historic_to_bar


def _bar(hour: int) -> CandleBar:
    return CandleBar(
        ts=datetime(2026, 10, 12, hour, 0, tzinfo=UTC),
        o=Decimal("100"),
        h=Decimal("101"),
        low=Decimal("99"),
        c=Decimal("100.5"),
        v=Decimal("10"),
    )


def test_repeat_fetch_does_not_duplicate() -> None:
    instrument_id = uuid4()
    first = new_candle_rows(instrument_id, "1h", [_bar(10), _bar(11)], set())
    assert len(first) == 2
    existing = {row.ts for row in first}
    second = new_candle_rows(
        instrument_id, "1h", [_bar(10), _bar(11), _bar(12)], existing
    )
    assert len(second) == 1
    assert second[0].ts == _bar(12).ts


def test_batch_dedupes_same_ts() -> None:
    instrument_id = uuid4()
    rows = new_candle_rows(instrument_id, "1h", [_bar(10), _bar(10)], set())
    assert len(rows) == 1


def test_historic_to_bar() -> None:
    q = SimpleNamespace(units=100, nano=0)
    raw = SimpleNamespace(
        time=datetime(2026, 10, 12, 10, 0, tzinfo=UTC),
        open=q,
        high=q,
        low=q,
        close=q,
        volume=7,
    )
    bar = historic_to_bar(raw)
    assert bar.v == Decimal("7")
    assert bar.o == Decimal("100")
