"""Сводка весов аллокатора для GET /allocation."""

from collections.abc import Mapping, Sequence
from decimal import Decimal

from app.alloc.capital import sleeve_capital
from app.alloc.weights_store import load_weights
from app.risk.sleeve import DEFAULT_SLEEVE_SHARE
from app.strategy.abs_mom import SLEEVE as ABS_MOM_SLEEVE
from app.strategy.abs_mom import SLEEVE_V2 as ABS_MOM2_SLEEVE
from app.strategy.abs_mom import SLEEVE_V3 as ABS_MOM3_SLEEVE
from app.strategy.abs_mom import SLEEVE_V4 as ABS_MOM4_SLEEVE
from app.strategy.abs_mom import SLEEVE_V5 as ABS_MOM5_SLEEVE
from app.strategy.donchian import SLEEVE as DONCHIAN_SLEEVE
from app.strategy.morning import SLEEVE as MORNING_SLEEVE
from app.strategy.overnight import SLEEVE as OVERNIGHT_SLEEVE
from app.strategy.rsi import SLEEVE as RSI_SLEEVE
from app.strategy.scalp import SLEEVE as SCALP_SLEEVE
from app.strategy.sma import SLEEVE as SMA_SLEEVE
from app.strategy.vol_scalp import SLEEVE as VOL_SCALP_SLEEVE

ACTIVE_SLEEVES = (
    SMA_SLEEVE,
    DONCHIAN_SLEEVE,
    RSI_SLEEVE,
    SCALP_SLEEVE,
    VOL_SCALP_SLEEVE,
    OVERNIGHT_SLEEVE,
    MORNING_SLEEVE,
    ABS_MOM_SLEEVE,
    ABS_MOM2_SLEEVE,
    ABS_MOM3_SLEEVE,
    ABS_MOM4_SLEEVE,
    ABS_MOM5_SLEEVE,
)


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
