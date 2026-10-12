"""Фильтр вселенной: неторгуемые бумаги получают active=false."""

from collections.abc import Mapping, Sequence
from uuid import UUID

from app.broker.trading_status import is_tradable
from app.models import UniverseMember


def apply_trading_filter(
    members: Sequence[UniverseMember],
    tradable: Mapping[UUID, bool],
) -> list[UniverseMember]:
    for member in members:
        member.active = bool(tradable.get(member.instrument_id, False))
    return list(members)


def tradable_map(
    statuses: Mapping[UUID, object],
) -> dict[UUID, bool]:
    return {instrument_id: is_tradable(raw) for instrument_id, raw in statuses.items()}
