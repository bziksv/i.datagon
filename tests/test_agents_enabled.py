from datetime import UTC, datetime

from app.agent.allocator import advise_weights
from app.agent.analyst import explain_signal
from app.agent.flag import DEFAULT_AGENTS_ENABLED, agents_enabled
from app.agent.rate import record_run_if_due
from app.models import SignalRow
from app.settings import Settings


def test_agents_off_by_default(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("TINKOFF_SANDBOX_TOKEN", "t")
    monkeypatch.setenv("APP_AUTH_TOKEN", "a")
    monkeypatch.setenv("AGENTS_ENABLED", "0")
    settings = Settings()
    assert settings.agents_enabled is False
    assert DEFAULT_AGENTS_ENABLED is False
    assert agents_enabled() is False
    signal = SignalRow(
        sleeve="sma_cross",
        ticker="SBER",
        ts=datetime(2026, 10, 12, tzinfo=UTC),
        kind="buy",
        payload={},
    )
    assert explain_signal(signal) is None
    assert advise_weights() == (None, None)
    assert (
        record_run_if_due(
            [],
            role="analyst",
            input="x",
            output="y",
            ts=signal.ts,
        )
        is None
    )
