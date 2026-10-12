"""Guardrails for allocation recommendations."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal


def cooldown_active(
    last_rebalance_at: datetime | None,
    *,
    now: datetime | None = None,
    cooldown: timedelta = timedelta(days=7),
) -> bool:
    if last_rebalance_at is None:
        return False
    current = now or datetime.now(UTC)
    changed = last_rebalance_at
    if changed.tzinfo is None:
        changed = changed.replace(tzinfo=UTC)
    return current - changed < cooldown


def constrain_weights(
    target: Mapping[str, Decimal],
    *,
    max_invested: Decimal,
    minimum: Decimal = Decimal("0.05"),
    maximum: Decimal = Decimal("0.30"),
    current: Mapping[str, Decimal] | None = None,
    max_step: Decimal = Decimal("0.10"),
) -> dict[str, Decimal]:
    """Apply per-sleeve floor/cap and optional turnover limit."""
    if not target:
        return {}
    bounded = {
        name: min(max(Decimal(value), minimum), maximum)
        for name, value in target.items()
    }
    total = sum(bounded.values(), Decimal("0"))
    if total > max_invested and total > 0:
        scale = max_invested / total
        bounded = {name: value * scale for name, value in bounded.items()}
    elif total < max_invested:
        remaining = max_invested - total
        while remaining > Decimal("0.000000000001"):
            available = {
                name: maximum - value
                for name, value in bounded.items()
                if value < maximum
            }
            if not available:
                break
            room = sum(available.values(), Decimal("0"))
            addition = min(remaining, room)
            for name, capacity in available.items():
                bounded[name] += addition * capacity / room
            remaining = max_invested - sum(bounded.values(), Decimal("0"))

    if current is not None:
        for name, value in list(bounded.items()):
            previous = Decimal(str(current.get(name, "0")))
            bounded[name] = min(
                max(value, max(previous - max_step, Decimal("0"))),
                previous + max_step,
                maximum,
            )
    total = sum(bounded.values(), Decimal("0"))
    if total > max_invested:
        scale = max_invested / total
        bounded = {name: value * scale for name, value in bounded.items()}
    return bounded
