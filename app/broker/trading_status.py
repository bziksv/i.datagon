"""Статус торгов. Воркер читает `tradable` и не ходит в ордера вне сессии."""

from typing import Any

TRADABLE_STATUSES = frozenset(
    {
        "SECURITY_TRADING_STATUS_NORMAL_TRADING",
        "SECURITY_TRADING_STATUS_DEALER_NORMAL_TRADING",
    }
)


def status_name(raw: Any) -> str:
    return getattr(raw, "name", None) or str(raw)


def is_tradable(raw: Any) -> bool:
    return status_name(raw) in TRADABLE_STATUSES


def trading_status_view(raw: Any) -> dict[str, object]:
    name = status_name(raw)
    return {"status": name, "tradable": name in TRADABLE_STATUSES}
