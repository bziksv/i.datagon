"""Сводка весов аллокатора для GET /allocation."""

from collections.abc import Mapping, Sequence
from decimal import Decimal

from app.alloc.capital import sleeve_capital
from app.alloc.weights_store import load_weights
from app.risk.sleeve import DEFAULT_SLEEVE_SHARE
from app.strategy.donchian import SLEEVE as DONCHIAN_SLEEVE
from app.strategy.rsi import SLEEVE as RSI_SLEEVE
from app.strategy.scalp import SLEEVE as SCALP_SLEEVE
from app.strategy.sma import SLEEVE as SMA_SLEEVE

ACTIVE_SLEEVES = (SMA_SLEEVE, DONCHIAN_SLEEVE, RSI_SLEEVE, SCALP_SLEEVE)


def _money(value: Decimal) -> float:
    return float(Decimal(value).quantize(Decimal("0.01")))


def allocation_view(
    sleeves: Sequence[str] = ACTIVE_SLEEVES,
    *,
    equity: Decimal,
    sleeve_share: Decimal = DEFAULT_SLEEVE_SHARE,
    weights: Mapping[str, Decimal] | None = None,
) -> dict:
    resolved = dict(weights) if weights is not None else load_weights(sleeves)
    items = []
    for name in sleeves:
        weight = Decimal(str(resolved.get(name, "0")))
        capital = sleeve_capital(
            equity, weight=weight, sleeve_share=sleeve_share
        )
        items.append(
            {
                "sleeve": name,
                "weight": float(weight),
                "capital": _money(capital),
            }
        )
    return {
        "sleeve_share": float(sleeve_share),
        "equity": _money(equity),
        "sleeves": items,
    }
