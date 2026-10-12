"""Аллокатор equal-weight: N=1 сейчас, формула готова к рукаву 2."""

from collections.abc import Sequence
from decimal import Decimal

from app.risk.sleeve import DEFAULT_SLEEVE_SHARE


def allocate(sleeves: Sequence[str]) -> dict[str, Decimal]:
    n = len(sleeves)
    if n == 0:
        return {}
    share = Decimal("1") / Decimal(n)
    return {name: share for name in sleeves}


def sleeve_capital(
    equity: Decimal,
    *,
    weight: Decimal = Decimal("1"),
    sleeve_share: Decimal = DEFAULT_SLEEVE_SHARE,
) -> Decimal:
    return Decimal(equity) * Decimal(sleeve_share) * Decimal(weight)
