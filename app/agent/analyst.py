"""Агент analyst: rationale по уже существующему signal. Ордер не создаёт."""

from app.agent.flag import agents_enabled
from app.agent.runs import record_run
from app.models import AgentRun, SignalRow

ROLE = "analyst"


class MissingSignalError(ValueError):
    pass


def rationale_for(signal: SignalRow) -> str:
    return (
        f"{signal.kind} {signal.ticker} on {signal.sleeve} "
        f"at {signal.ts.isoformat()}"
    )


def explain_signal(
    signal: SignalRow | None,
    *,
    enabled: bool | None = None,
) -> AgentRun | None:
    if not agents_enabled(enabled):
        return None
    if signal is None:
        raise MissingSignalError("signal required")
    prompt = (
        f"Explain existing signal sleeve={signal.sleeve} "
        f"ticker={signal.ticker} kind={signal.kind} ts={signal.ts.isoformat()}"
    )
    return record_run(
        role=ROLE,
        input=prompt,
        output=rationale_for(signal),
        ts=signal.ts,
        secrets=(),
    )
