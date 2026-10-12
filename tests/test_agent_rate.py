from datetime import UTC, datetime, timedelta

from app.agent.rate import DEFAULT_INTERVAL_SEC, record_run_if_due
from app.agent.runs import record_run


def _ts(minute: int) -> datetime:
    return datetime(2026, 10, 12, 15, minute, tzinfo=UTC)


def test_spam_on_same_bar_blocked() -> None:
    first = record_run_if_due(
        [],
        role="analyst",
        input="bar-1",
        output="ok",
        ts=_ts(0),
        bar=_ts(0),
        enabled=True,
    )
    assert first is not None
    again = record_run_if_due(
        [first],
        role="analyst",
        input="bar-1-again",
        output="spam",
        ts=_ts(0),
        bar=_ts(0),
        enabled=True,
    )
    assert again is None


def test_next_bar_after_interval_allowed() -> None:
    first = record_run(
        role="analyst",
        input="bar-1",
        output="ok",
        ts=_ts(0),
        secrets=(),
    )
    too_soon = record_run_if_due(
        [first],
        role="analyst",
        input="bar-2",
        output="soon",
        ts=_ts(0) + timedelta(minutes=5),
        bar=_ts(0) + timedelta(minutes=5),
        interval_sec=DEFAULT_INTERVAL_SEC,
        enabled=True,
    )
    assert too_soon is None
    later = record_run_if_due(
        [first],
        role="analyst",
        input="bar-2",
        output="ok",
        ts=_ts(0) + timedelta(minutes=15),
        bar=_ts(0) + timedelta(minutes=15),
        interval_sec=DEFAULT_INTERVAL_SEC,
        enabled=True,
    )
    assert later is not None
    assert later.output == "ok"
