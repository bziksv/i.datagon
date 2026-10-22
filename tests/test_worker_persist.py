from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import SignalRow
from worker.persist import persist_signals


def test_persist_signals_noop_on_empty() -> None:
    assert persist_signals([]) == 0


def _signal(ticker: str) -> SignalRow:
    return SignalRow(
        sleeve="sma_cross",
        ticker=ticker,
        ts=datetime(2026, 10, 12, tzinfo=UTC),
        kind="buy",
        payload={},
    )


def test_persist_signals_skips_already_saved_bars() -> None:
    old, new = _signal("SBER"), _signal("GAZP")
    session = MagicMock()
    session.execute = AsyncMock(return_value=[("sma_cross", "SBER", old.ts)])
    session.commit = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    maker = MagicMock(return_value=session)
    with patch("worker.persist.get_sessionmaker", return_value=maker):
        assert persist_signals([old, new, _signal("GAZP")]) == 1
    session.add_all.assert_called_once_with([new])
    session.commit.assert_awaited_once()


def test_worker_uses_one_event_loop_for_all_database_writes() -> None:
    source = (Path(__file__).parents[1] / "worker" / "__main__.py").read_text()
    assert source.count("asyncio.run(") == 1
    assert "asyncio.run(run_worker())" in source
    assert "await persist_valuation_snapshot" in source
    assert "await persist_signals_async" in source
    assert "CANDLE_REFRESH_INTERVAL_SEC" in source
    assert "await asyncio.to_thread(" in source
    assert "refresh_candles" in source
