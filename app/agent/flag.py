"""Выключатель агентов. По умолчанию выключены — этап 0 молчит."""

from __future__ import annotations

import os

DEFAULT_AGENTS_ENABLED = False


def agents_enabled(enabled: bool | None = None) -> bool:
    if enabled is not None:
        return bool(enabled)
    raw = os.environ.get("AGENTS_ENABLED", "0").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off", ""}:
        return DEFAULT_AGENTS_ENABLED
    return DEFAULT_AGENTS_ENABLED
