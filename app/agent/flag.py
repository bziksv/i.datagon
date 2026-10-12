"""Выключатель агентов. По умолчанию выключены — этап 0 молчит."""

DEFAULT_AGENTS_ENABLED = False


def agents_enabled(enabled: bool | None = None) -> bool:
    if enabled is None:
        return DEFAULT_AGENTS_ENABLED
    return bool(enabled)
