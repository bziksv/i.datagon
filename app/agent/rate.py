"""Лимит частоты агента: раз на бар и не чаще чем раз в N минут."""

from collections.abc import Sequence
from datetime import datetime

from app.agent.flag import agents_enabled
from app.agent.runs import record_run
from app.models import AgentRun

DEFAULT_INTERVAL_SEC = 15 * 60


def last_run(runs: Sequence[AgentRun], role: str) -> AgentRun | None:
    matched = [row for row in runs if row.role == role]
    if not matched:
        return None
    return max(matched, key=lambda row: row.ts)


def agent_due(
    last: datetime | None,
    now: datetime,
    *,
    last_bar: datetime | None = None,
    bar: datetime | None = None,
    interval_sec: int = DEFAULT_INTERVAL_SEC,
) -> bool:
    if bar is not None and last_bar is not None and bar == last_bar:
        return False
    if last is None:
        return True
    return (now - last).total_seconds() >= interval_sec


def record_run_if_due(
    existing: Sequence[AgentRun],
    *,
    role: str,
    input: str,
    output: str,
    ts: datetime,
    bar: datetime | None = None,
    interval_sec: int = DEFAULT_INTERVAL_SEC,
    enabled: bool | None = None,
) -> AgentRun | None:
    if not agents_enabled(enabled):
        return None
    prev = last_run(existing, role)
    if not agent_due(
        prev.ts if prev else None,
        ts,
        last_bar=prev.ts if prev else None,
        bar=bar if bar is not None else ts,
        interval_sec=interval_sec,
    ):
        return None
    return record_run(role=role, input=input, output=output, ts=ts, secrets=())
