import inspect
from datetime import UTC, datetime

import pytest

from app.agent import analyst
from app.agent.analyst import MissingSignalError, explain_signal
from app.models import AgentRun, SignalRow


def _signal() -> SignalRow:
    return SignalRow(
        sleeve="sma_cross",
        ticker="SBER",
        ts=datetime(2026, 10, 12, 15, 50, tzinfo=UTC),
        kind="buy",
        payload={},
    )


def test_analyst_writes_text_only() -> None:
    row = explain_signal(_signal(), enabled=True)
    assert isinstance(row, AgentRun)
    assert row.role == "analyst"
    assert row.output
    assert "SBER" in row.output
    assert "buy" in row.output
    assert isinstance(row.output, str)
    assert isinstance(row.input, str)


def test_analyst_needs_existing_signal() -> None:
    with pytest.raises(MissingSignalError):
        explain_signal(None, enabled=True)


def test_analyst_does_not_create_order() -> None:
    source = inspect.getsource(analyst)
    assert "place_order" not in source
    assert "draft_order" not in source
    assert "new_proposal" not in source
    assert "Order(" not in source
