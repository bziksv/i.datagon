from datetime import UTC, datetime

from app.agent.runs import REDACTED, record_run, redact_prompt
from app.models import AgentRun


def test_prompt_strips_broker_token() -> None:
    fake = "t." + ("A" * 20)
    prompt = f"role=analyst token={fake} ticker=SBER"
    row = record_run(
        role="analyst",
        input=prompt,
        output="hold",
        ts=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
        secrets=[fake],
    )
    assert isinstance(row, AgentRun)
    assert row.role == "analyst"
    assert row.output == "hold"
    assert fake not in row.input
    assert "SBER" in row.input
    assert REDACTED in row.input
    assert AgentRun.__tablename__ == "agent_runs"


def test_env_token_is_redacted() -> None:
    secret = "sandbox-secret-value"
    text = redact_prompt(
        f"TINKOFF_SANDBOX_TOKEN={secret}",
        [secret],
    )
    assert secret not in text
    assert REDACTED in text
