"""Джоба: выгрузить акции MOEX в instruments."""

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.broker.instruments import dump_moex_instruments

from app.models import Fundamental, Instrument, UniverseMember
from app.universe.cap import apply_universe_cap
from app.universe.currency import apply_currency_lot_filter
from app.universe.fundamentals import apply_fundamentals_filter
from app.universe.liquidity import LiquidityQuote, apply_liquidity_filter
from app.universe.reason import ReasonFacts, apply_reasons
from app.universe.trading import apply_trading_filter, tradable_map


def run_moex_dump(
    existing: Sequence[Instrument],
    shares: Sequence[Any],
) -> list[Instrument]:
    return dump_moex_instruments(existing, shares)


def mark_tradable(
    members: Sequence[UniverseMember],
    statuses: Mapping[UUID, object],
) -> list[UniverseMember]:
    return apply_trading_filter(members, tradable_map(statuses))


def mark_rub_lots(
    members: Sequence[UniverseMember],
    instruments: Sequence[Instrument],
) -> list[UniverseMember]:
    return apply_currency_lot_filter(members, instruments)


def mark_liquid(
    members: Sequence[UniverseMember],
    quotes: Mapping[UUID, LiquidityQuote],
    *,
    min_turnover: Decimal,
    max_spread_bps: Decimal,
) -> list[UniverseMember]:
    return apply_liquidity_filter(
        members,
        quotes,
        min_turnover=min_turnover,
        max_spread_bps=max_spread_bps,
    )


def mark_fundamentals(
    members: Sequence[UniverseMember],
    instruments: Sequence[Instrument],
    snaps: Sequence[Fundamental],
    *,
    enabled: bool,
) -> list[UniverseMember]:
    return apply_fundamentals_filter(
        members, instruments, snaps, enabled=enabled
    )


def cap_universe(
    members: Sequence[UniverseMember],
    scores: Mapping[UUID, Decimal] | None = None,
    *,
    limit: int,
) -> list[UniverseMember]:
    return apply_universe_cap(members, scores, limit=limit)


def explain_universe(
    members: Sequence[UniverseMember],
    facts: Mapping[UUID, ReasonFacts],
) -> list[UniverseMember]:
    return apply_reasons(members, facts)
