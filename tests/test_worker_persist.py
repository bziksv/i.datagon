from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import SignalRow
from worker.persist import persist_signals


def test_persist_signals_noop_on_empty() -> None:
    assert persist_signals([]) == 0


def test_persist_signals_commits_rows() -> None:
    row = SignalRow(
        sleeve="sma_cross",
        ticker="SBER",
        ts=datetime(2026, 10, 12, tzinfo=UTC),
        kind="buy",
        payload={},
    )
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    maker = MagicMock(return_value=session)
    with patch("worker.persist.get_sessionmaker", return_value=maker):
        assert persist_signals([row]) == 1
    session.add.assert_called_once_with(row)
    session.commit.assert_awaited_once()


def test_worker_uses_one_event_loop_for_all_database_writes() -> None:
    source = (Path(__file__).parents[1] / "worker" / "__main__.py").read_text()
    assert source.count("asyncio.run(") == 1
    assert "asyncio.run(run_worker())" in source
    assert "await persist_valuation_snapshot" in source
    assert "await persist_signals_async" in source
