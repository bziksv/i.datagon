"""Журнал прогонов агента: промпт в input без токенов брокера."""

import os
import re
from collections.abc import Sequence
from datetime import UTC, datetime

from app.models import AgentRun

REDACTED = "[redacted]"
_BROKER_TOKEN = re.compile(r"t\.[A-Za-z0-9_-]{16,}")


def broker_secrets(env: dict[str, str] | None = None) -> list[str]:
    source = env if env is not None else os.environ
    secrets: list[str] = []
    for key in ("TINKOFF_SANDBOX_TOKEN", "TINKOFF_LIVE"):
        value = (source.get(key) or "").strip()
        if value:
            secrets.append(value)
    return secrets


def redact_prompt(text: str, secrets: Sequence[str] = ()) -> str:
    redacted = text
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, REDACTED)
    return _BROKER_TOKEN.sub(REDACTED, redacted)


def record_run(
    *,
    role: str,
    input: str,
    output: str,
    ts: datetime | None = None,
    secrets: Sequence[str] | None = None,
) -> AgentRun:
    hidden = list(secrets) if secrets is not None else broker_secrets()
    return AgentRun(
        role=role,
        input=redact_prompt(input, hidden),
        output=output,
        ts=ts or datetime.now(UTC),
    )
