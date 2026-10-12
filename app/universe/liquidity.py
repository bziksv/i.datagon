"""Фильтр ликвидности: оборот и спред. Пороги из конфига."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.models import UniverseMember

DEFAULT_MIN_TURNOVER = Decimal("10000000")
DEFAULT_MAX_SPREAD_BPS = Decimal("50")


@dataclass(frozen=True)
class LiquidityQuote:
    turnover: Decimal
    spread_bps: Decimal


def is_liquid(
    quote: LiquidityQuote,
    *,
    min_turnover: Decimal = DEFAULT_MIN_TURNOVER,
    max_spread_bps: Decimal = DEFAULT_MAX_SPREAD_BPS,
) -> bool:
    return quote.turnover >= min_turnover and quote.spread_bps <= max_spread_bps


def apply_liquidity_filter(
    members: Sequence[UniverseMember],
    quotes: Mapping[UUID, LiquidityQuote],
    *,
    min_turnover: Decimal = DEFAULT_MIN_TURNOVER,
    max_spread_bps: Decimal = DEFAULT_MAX_SPREAD_BPS,
) -> list[UniverseMember]:
    for member in members:
        quote = quotes.get(member.instrument_id)
        if quote is None or not is_liquid(
            quote, min_turnover=min_turnover, max_spread_bps=max_spread_bps
        ):
            member.active = False
    return list(members)
