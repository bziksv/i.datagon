"""Потолок вселенной: UNIVERSE_MAX из конфига. Сито не снимается."""

from collections.abc import Mapping, Sequence
from decimal import Decimal
from uuid import UUID

from app.models import UniverseMember

DEFAULT_UNIVERSE_MAX = 30


def resolve_universe_max(
    value: int | None,
    default: int = DEFAULT_UNIVERSE_MAX,
) -> int:
    if value is None:
        return default
    limit = int(value)
    if limit < 1:
        return default
    return limit


def apply_universe_cap(
    members: Sequence[UniverseMember],
    scores: Mapping[UUID, Decimal] | None = None,
    *,
    limit: int = DEFAULT_UNIVERSE_MAX,
) -> list[UniverseMember]:
    active = [row for row in members if row.active]
    ranking = scores or {}
    active.sort(
        key=lambda row: ranking.get(row.instrument_id, Decimal("0")),
        reverse=True,
    )
    for extra in active[limit:]:
        extra.active = False
    return list(members)
