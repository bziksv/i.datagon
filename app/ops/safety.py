"""Fail-closed startup checks: этот репозиторий остаётся paper/sandbox."""

from __future__ import annotations

import os
from collections.abc import Mapping

LIVE_FORBIDDEN = "live trading is forbidden in paper build"
_TRUE = frozenset({"1", "true", "yes", "on"})


def assert_paper_mode(env: Mapping[str, str] | None = None) -> None:
    values = env if env is not None else os.environ
    if str(values.get("TINKOFF_LIVE", "0")).strip().lower() in _TRUE:
        raise RuntimeError(LIVE_FORBIDDEN)
