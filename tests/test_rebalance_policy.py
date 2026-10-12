from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.alloc.rebalance import constrain_weights, cooldown_active


def test_rebalance_constraints_apply_floor_cap_and_cash_reserve() -> None:
    weights = constrain_weights(
        {"a": Decimal("0.49"), "b": Decimal("0.01")},
        max_invested=Decimal("0.50"),
    )
    assert sum(weights.values(), Decimal("0")) == Decimal("0.50")
    assert weights["a"] <= Decimal("0.30")
    assert weights["b"] >= Decimal("0.05")


def test_rebalance_step_limits_turnover() -> None:
    weights = constrain_weights(
        {"a": Decimal("0.30"), "b": Decimal("0.20")},
        max_invested=Decimal("0.50"),
        current={"a": Decimal("0.10"), "b": Decimal("0.20")},
        max_step=Decimal("0.05"),
    )
    assert weights["a"] == Decimal("0.15")
    assert weights["b"] == Decimal("0.20")


def test_rebalance_cooldown_is_explicit() -> None:
    now = datetime(2026, 10, 12, tzinfo=UTC)
    assert cooldown_active(
        now - timedelta(days=2),
        now=now,
        cooldown=timedelta(days=7),
    )
    assert not cooldown_active(
        now - timedelta(days=8),
        now=now,
        cooldown=timedelta(days=7),
    )
